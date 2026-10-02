from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql.types import *

spark = (SparkSession.builder.appName("TransitPulse")
    .config("spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.postgresql:postgresql:42.7.3")
    .config("spark.sql.shuffle.partitions", "4")
    .getOrCreate())
spark.sparkContext.setLogLevel("WARN")

schema = StructType([
    StructField("ts", StringType()), StructField("route", StringType()),
    StructField("station", StringType()), StructField("delay_min", DoubleType()),
    StructField("weather", StringType()), StructField("injected", BooleanType()),
    StructField("produced_at_ms", DoubleType()),
])

raw = (spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "localhost:9092")
    .option("subscribe", "transit-events")
    .option("startingOffsets", "earliest")
    .option("maxOffsetsPerTrigger", 5000)
    .load())

events = (raw.select(F.from_json(F.col("value").cast("string"), schema).alias("e"))
    .select("e.*").withColumn("ts", F.to_timestamp("ts")))

THRESHOLD = 2.5
JDBC = "jdbc:postgresql://localhost:5432/transitpulse"
PROPS = {"user": "transit", "password": "transit", "driver": "org.postgresql.Driver"}

def process(df, batch_id):
    if df.isEmpty():
        return
    w = Window.partitionBy("route")
    out = (df
        .withColumn("mean", F.avg("delay_min").over(w))
        .withColumn("std", F.stddev("delay_min").over(w))
        .withColumn("zscore", F.when(F.col("std") > 0,
                    (F.col("delay_min") - F.col("mean")) / F.col("std")).otherwise(0.0))
        .withColumn("is_anomaly", F.col("zscore") > THRESHOLD)
        .withColumn("latency_ms", F.current_timestamp().cast("double") * 1000 - F.col("produced_at_ms"))
        .select("ts", "route", "station", "delay_min", "weather",
                "zscore", "is_anomaly", "injected", "latency_ms"))
    out.write.jdbc(JDBC, "events", mode="append", properties=PROPS)

(events.writeStream.foreachBatch(process)
    .option("checkpointLocation", "./checkpoint")
    .start().awaitTermination())