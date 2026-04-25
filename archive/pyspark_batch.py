import pyspark
from pyspark.sql import SparkSession

spark = SparkSession.builder.master("local[*]").appName("test").getOrCreate()
sc = spark.sparkContext

sc.setLogLevel("ERROR")

print(f"Spark version: {spark.version}")

df = spark.range(10)
df.show()

spark.stop()
