#!/usr/bin/env bash
# Registers a task-definition revision that runs the given image and rolls
# the lending service onto it. Usage: ops/release.sh <image-uri>
set -euo pipefail
image="${1:?usage: release.sh <image-uri>}"
current="$(aws ecs describe-services --cluster library --services lending --query 'services[0].taskDefinition' --output text)"
aws ecs describe-task-definition --task-definition "$current" --query taskDefinition --output json \
  | jq --arg image "$image" '.containerDefinitions[0].image = $image
      | {family, containerDefinitions, executionRoleArn, taskRoleArn, networkMode, requiresCompatibilities, cpu, memory}' \
  > /tmp/task-definition.json
revision="$(aws ecs register-task-definition --cli-input-json file:///tmp/task-definition.json --query 'taskDefinition.taskDefinitionArn' --output text)"
aws ecs update-service --cluster library --service lending --task-definition "$revision"
