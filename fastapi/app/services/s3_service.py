import boto3
import io
from dotenv import load_dotenv
import os

load_dotenv()

s3 = boto3.client(
    's3',
    aws_access_key_id=os.getent('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    endpoint_url=os.getenv('S3_ENDPOINT_URL')
)

def upload_to_s3(df):
    bucket_name = os.getenv('S3_BUCKET_NAME')
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)

    file_name = f"inmet_{os.getenv('AWS_DEFAULT_REGION')}.csv"

    s3.put_object(
        Bucket = bucket_name,
        Key = f"raw/{file_name}",
        Body = csv_buffer.getvalue(),
        ContentType = "text/csv"
    )

    return f"s3://{bucket_name}/raw/{file_name}"