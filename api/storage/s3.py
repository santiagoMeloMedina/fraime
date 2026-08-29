import boto3
from fastapi import HTTPException, status

# How long a presigned GET URL for a generated video stays valid.
_PRESIGNED_URL_EXPIRES_IN_SECONDS = 3600


def _client():
    return boto3.client("s3")


def probe_write_access(bucket: str, key: str) -> None:
    """Confirms `key` can be written before generation starts, so a permissions
    problem fails fast instead of after several minutes of video generation."""
    try:
        _client().put_object(Bucket=bucket, Key=key, Body=b"")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No access to s3://{bucket}/{key}",
        ) from e


def upload_file(bucket: str, key: str, path: str) -> None:
    _client().upload_file(path, bucket, key)


def generate_presigned_url(bucket: str, key: str) -> str:
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=_PRESIGNED_URL_EXPIRES_IN_SECONDS,
    )
