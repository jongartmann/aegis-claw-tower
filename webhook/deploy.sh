#!/bin/bash
cd /root/aegis-claw-tower
git pull origin main
docker compose up -d --build
echo "Deployed at $(date)" >> /root/webhook/deploy.log
