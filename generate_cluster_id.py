#!/usr/bin/env python3
"""
Generate a new Kafka KRaft CLUSTER_ID
This creates a base64-encoded UUID suitable for Kafka KRaft mode
"""
import uuid
import base64

# Generate a UUID
cluster_uuid = uuid.uuid4()

# Convert to bytes (16 bytes)
uuid_bytes = cluster_uuid.bytes

# Encode to base64 and remove padding
cluster_id = base64.b64encode(uuid_bytes).decode('utf-8').rstrip('=')

print("=" * 60)
print("New Kafka KRaft CLUSTER_ID Generated")
print("=" * 60)
print(f"\nCLUSTER_ID: \"{cluster_id}\"")
print(f"\nUUID: {cluster_uuid}")
print("\nAdd this to your docker-compose.yml:")
print(f'      CLUSTER_ID: "{cluster_id}"')
print("\n⚠️  Note: If Kafka is already running, you'll need to:")
print("   1. Stop all services: docker-compose down -v")
print("   2. Update docker-compose.yml with the new CLUSTER_ID")
print("   3. Start services again: docker-compose up -d")
print("=" * 60)

