import airflow
from airflow import DAG,models
from datetime import datetime,timedelta
from airflow.operators.bash_operator import BashOperator
from airflow.contrib.operators import dataproc_operator
from airflow.providers.google.cloud.sensors.gcs 
import GCSObjectExistenceSensor
#Define pyspark file location and inbound bucket
spark_file = ('gs://sample_test_hema/testproj.py')
inbound_bucket = models.Variable.get('inbound_bucket')
#DAG default arguments
default_arguments = {'start_date':airflow.utils.dates.days_ago(1),
'retries':1,	
'retries_delay':timedelta(minutes=1)
}
#Define DAG
dag = DAG('dataproc_spark_pipeline',
description='DataProc-Spark-Pipeline',
schedule_interval=timedelta(days=1),
default_args=default_arguments)
#File Sensor Event Task
check_inbound_file = GCSObjectExistenceSensor(task_id='check_inbound_file',
bucket=inbound_bucket,
object='part-00000-d326e1da-15af-4cb2-8f5d-b8d04887d522-c000.csv',
dag=dag)
#Create DataProc Spark Cluster
create_cluster = dataproc_operator.DataprocClusterCreateOperator(
task_id='create_cluster',
dag=dag,
region=models.Variable.get('dataproc_region'),
zone=models.Variable.get('dataproc_zone'),
project_id=models.Variable.get('project_id'),
cluster_name='dataproc-spark-pipeline-{{ds}}',
num_workers=2,
master_machine_type='n1-standard-2',
worker_machine_type='n1-standard-2')
#Submit Spark job 
spark_transformation = dataproc_operator.DataProcPySparkOperator(
task_id='spark_transformation',
main=spark_file,job_name='spark-transformations',
region=models.Variable.get('dataproc_region'),
zone=models.Variable.get('dataproc_zone'),
project_id=models.Variable.get('project_id'),
cluster_name='dataproc-spark-pipeline-{{ds}}',
dag=dag)
#Delete DataProc Spark Cluster
delete_cluster = dataproc_operator.DataprocClusterDeleteOperator(
task_id='delete_cluster',
dag=dag,
project_id=models.Variable.get('project_id'),
region=models.Variable.get('dataproc_region'),
zone=models.Variable.get('dataproc_zone'),
cluster_name='dataproc-spark-pipeline-{{ds}}')
#Delete Processed files
remove_files = BashOperator(task_id='remove_files',
bash_command='gsutil rm gs://sample_test_hema/part-00000-d326e1da-15af-4cb2-8f5d-b8d04887d522-c000.csv',
dag=dag)
start = BashOperator(task_id='start',
bash_command='echo date',
dag=dag)
end = BashOperator(task_id='end',
bash_command='echo date',
dag=dag)
sleep_process = BashOperator(task_id='sleep',
bash_command='sleep 30',
dag=dag)
#ETL pipeline 
start>>check_inbound_file
>>create_cluster
>>sleep_process
>>spark_transformation
>>delete_cluster
>>remove_files
>>end

