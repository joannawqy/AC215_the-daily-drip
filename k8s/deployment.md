docker tag the-daily-drip-app:latest gcr.io/ac215-480602/the-daily-drip-app:latest

docker push gcr.io/ac215-480602/the-daily-drip-app:latest

kubectl apply -f k8s/deployment.yaml