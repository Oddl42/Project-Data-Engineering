#!/usr/bin/env bash

# Name des Clusters
CLUSTER_NAME="local-spark-cluster"

# YAML-Datei für das Cluster erstellen
cat <<EOF > kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: $CLUSTER_NAME
nodes:
  - role: control-plane
    # Optionaler Port-Forward zum lokalen Host, z.B. für API-Zugriff:
    # extraPortMappings:
    #   - containerPort: 30080
    #     hostPort: 8080
    #     protocol: TCP
  - role: worker
  - role: worker
EOF

echo "Erzeuge lokales Kubernetes-Cluster '$CLUSTER_NAME' mit 1 Master und 2 Worker-Nodes ..."
kind create cluster --config kind-config.yaml

echo "Überprüfe erstellte Cluster-Ressourcen ..."
kubectl get nodes

echo "Fertig! Du hast jetzt ein lokales K8s-Cluster mit Master- und Worker-Nodes.