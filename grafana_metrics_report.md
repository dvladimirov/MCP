# Kubernetes Simulator Metrics Report

Generated on 2025-03-12 23:34:28

Simulating 5 pods across 3 namespaces

## Metrics Summary

| Category | Count |
|----------|-------|
| container | 205 |
| kube | 97 |
| **Total** | **302** |

## Metric Details by Category

### container

```
container_cpu_cfs_periods_total{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",pod_name="nginx-1248",kubernetes_io_hostname="master-1"} 362730
container_cpu_cfs_periods_total{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",pod_name="nginx-5767",kubernetes_io_hostname="worker-2"} 46970
container_cpu_cfs_periods_total{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",pod_name="postgres-7229",kubernetes_io_hostname="worker-2"} 637620
container_cpu_cfs_periods_total{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 152520
container_cpu_cfs_periods_total{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",pod_name="redis-9302",kubernetes_io_hostname="worker-2"} 120230
container_cpu_cfs_throttled_periods_total{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",pod_name="nginx-1248",kubernetes_io_hostname="master-1"} 9
container_cpu_cfs_throttled_periods_total{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",pod_name="nginx-5767",kubernetes_io_hostname="worker-2"} 18
container_cpu_cfs_throttled_periods_total{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",pod_name="postgres-7229",kubernetes_io_hostname="worker-2"} 38
container_cpu_cfs_throttled_periods_total{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 19
container_cpu_cfs_throttled_periods_total{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",pod_name="redis-9302",kubernetes_io_hostname="worker-2"} 2
container_cpu_load_average_10s{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",pod_name="nginx-1248",kubernetes_io_hostname="master-1"} 0.10685875501449539
container_cpu_load_average_10s{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",pod_name="nginx-5767",kubernetes_io_hostname="worker-2"} 0.20120650556552114
container_cpu_load_average_10s{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",pod_name="postgres-7229",kubernetes_io_hostname="worker-2"} 0.42397861177819696
container_cpu_load_average_10s{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 0.20938717311022564
container_cpu_load_average_10s{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",pod_name="redis-9302",kubernetes_io_hostname="worker-2"} 0.02752621761790051
container_cpu_system_seconds_total{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",pod_name="nginx-1248",kubernetes_io_hostname="master-1"} 1057.1148166701607
container_cpu_system_seconds_total{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",pod_name="nginx-5767",kubernetes_io_hostname="worker-2"} 257.7455595863043
container_cpu_system_seconds_total{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",pod_name="postgres-7229",kubernetes_io_hostname="worker-2"} 7372.833922743976
container_cpu_system_seconds_total{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 870.9745161220387
container_cpu_system_seconds_total{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",pod_name="redis-9302",kubernetes_io_hostname="worker-2"} 90.25847161593326
container_cpu_usage_seconds_rate{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",pod_name="nginx-1248",kubernetes_io_hostname="master-1"} 0.09714432274045035
container_cpu_usage_seconds_rate{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",pod_name="nginx-5767",kubernetes_io_hostname="worker-2"} 0.18291500505956465
container_cpu_usage_seconds_rate{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",pod_name="postgres-7229",kubernetes_io_hostname="worker-2"} 0.38543510161654265
container_cpu_usage_seconds_rate{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 0.19035197555475056
container_cpu_usage_seconds_rate{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",pod_name="redis-9302",kubernetes_io_hostname="worker-2"} 0.02502383419809137
container_cpu_usage_seconds_total{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",pod_name="nginx-1248",kubernetes_io_hostname="master-1"} 3523.716054779728
container_cpu_usage_seconds_total{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",pod_name="nginx-5767",kubernetes_io_hostname="worker-2"} 859.1518647207466
container_cpu_usage_seconds_total{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",pod_name="postgres-7229",kubernetes_io_hostname="worker-2"} 24576.11307369967
container_cpu_usage_seconds_total{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 2903.2483854396587
container_cpu_usage_seconds_total{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",pod_name="redis-9302",kubernetes_io_hostname="worker-2"} 300.86157199941556
container_cpu_user_seconds_total{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",pod_name="nginx-1248",kubernetes_io_hostname="master-1"} 2466.601238978105
container_cpu_user_seconds_total{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",pod_name="nginx-5767",kubernetes_io_hostname="worker-2"} 601.4063057929584
container_cpu_user_seconds_total{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",pod_name="postgres-7229",kubernetes_io_hostname="worker-2"} 17203.279153262258
container_cpu_user_seconds_total{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 2032.2738711102659
container_cpu_user_seconds_total{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",pod_name="redis-9302",kubernetes_io_hostname="worker-2"} 210.6031004538828
container_file_descriptors{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",pod_name="nginx-1248",kubernetes_io_hostname="master-1"} 35
container_file_descriptors{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",pod_name="nginx-5767",kubernetes_io_hostname="worker-2"} 165
container_file_descriptors{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",pod_name="postgres-7229",kubernetes_io_hostname="worker-2"} 70
container_file_descriptors{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 144
container_file_descriptors{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",pod_name="redis-9302",kubernetes_io_hostname="worker-2"} 90
container_fs_io_current{container_name="nginx-1248",container="nginx-1248",device="pod",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",kubernetes_io_hostname="master-1"} 6
container_fs_io_current{container_name="nginx-5767",container="nginx-5767",device="pod",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",kubernetes_io_hostname="worker-2"} 4
container_fs_io_current{container_name="postgres-7229",container="postgres-7229",device="pod",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",kubernetes_io_hostname="worker-2"} 4
container_fs_io_current{container_name="redis-9216",container="redis-9216",device="pod",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1"} 0
container_fs_io_current{container_name="redis-9302",container="redis-9302",device="pod",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",kubernetes_io_hostname="worker-2"} 0
container_fs_io_time_seconds_total{container_name="nginx-1248",container="nginx-1248",device="pod",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",kubernetes_io_hostname="master-1"} 2337.811113347071
container_fs_io_time_seconds_total{container_name="nginx-5767",container="nginx-5767",device="pod",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",kubernetes_io_hostname="worker-2"} 212.16536705258017
container_fs_io_time_seconds_total{container_name="postgres-7229",container="postgres-7229",device="pod",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",kubernetes_io_hostname="worker-2"} 2607.06224384265
container_fs_io_time_seconds_total{container_name="redis-9216",container="redis-9216",device="pod",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1"} 103.31951809980389
container_fs_io_time_seconds_total{container_name="redis-9302",container="redis-9302",device="pod",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",kubernetes_io_hostname="worker-2"} 68.9384472783425
container_fs_limit_bytes{container_name="nginx-1248",container="nginx-1248",device="pod",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",kubernetes_io_hostname="master-1"} 10737418240
container_fs_limit_bytes{container_name="nginx-5767",container="nginx-5767",device="pod",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",kubernetes_io_hostname="worker-2"} 10737418240
container_fs_limit_bytes{container_name="postgres-7229",container="postgres-7229",device="pod",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",kubernetes_io_hostname="worker-2"} 10737418240
container_fs_limit_bytes{container_name="redis-9216",container="redis-9216",device="pod",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1"} 10737418240
container_fs_limit_bytes{container_name="redis-9302",container="redis-9302",device="pod",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",kubernetes_io_hostname="worker-2"} 10737418240
container_fs_reads_bytes_total{container_name="nginx-1248",container="nginx-1248",device="pod",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",kubernetes_io_hostname="master-1"} 21404105494
container_fs_reads_bytes_total{container_name="nginx-5767",container="nginx-5767",device="pod",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",kubernetes_io_hostname="worker-2"} 1855651951
container_fs_reads_bytes_total{container_name="postgres-7229",container="postgres-7229",device="pod",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",kubernetes_io_hostname="worker-2"} 8702184992
container_fs_reads_bytes_total{container_name="redis-9216",container="redis-9216",device="pod",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1"} 856547908
container_fs_reads_bytes_total{container_name="redis-9302",container="redis-9302",device="pod",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",kubernetes_io_hostname="worker-2"} 573107316
container_fs_reads_total{container_name="nginx-1248",container="nginx-1248",device="pod",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",kubernetes_io_hostname="master-1"} 5225611
container_fs_reads_total{container_name="nginx-5767",container="nginx-5767",device="pod",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",kubernetes_io_hostname="worker-2"} 453040
container_fs_reads_total{container_name="postgres-7229",container="postgres-7229",device="pod",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",kubernetes_io_hostname="worker-2"} 2124556
container_fs_reads_total{container_name="redis-9216",container="redis-9216",device="pod",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1"} 209118
container_fs_reads_total{container_name="redis-9302",container="redis-9302",device="pod",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",kubernetes_io_hostname="worker-2"} 139918
container_fs_usage_bytes{container_name="nginx-1248",container="nginx-1248",device="pod",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",kubernetes_io_hostname="master-1"} 36273000396
container_fs_usage_bytes{container_name="nginx-5767",container="nginx-5767",device="pod",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",kubernetes_io_hostname="worker-2"} 4697000487
container_fs_usage_bytes{container_name="postgres-7229",container="postgres-7229",device="pod",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",kubernetes_io_hostname="worker-2"} 63762000344
container_fs_usage_bytes{container_name="redis-9216",container="redis-9216",device="pod",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1"} 15252000313
container_fs_usage_bytes{container_name="redis-9302",container="redis-9302",device="pod",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",kubernetes_io_hostname="worker-2"} 12023000555
container_fs_writes_bytes_total{container_name="nginx-1248",container="nginx-1248",device="pod",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",kubernetes_io_hostname="master-1"} 1974005635
container_fs_writes_bytes_total{container_name="nginx-5767",container="nginx-5767",device="pod",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",kubernetes_io_hostname="worker-2"} 266001717
container_fs_writes_bytes_total{container_name="postgres-7229",container="postgres-7229",device="pod",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",kubernetes_io_hostname="worker-2"} 17368437444
container_fs_writes_bytes_total{container_name="redis-9216",container="redis-9216",device="pod",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1"} 176647272
container_fs_writes_bytes_total{container_name="redis-9302",container="redis-9302",device="pod",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",kubernetes_io_hostname="worker-2"} 116277156
container_fs_writes_total{container_name="nginx-1248",container="nginx-1248",device="pod",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",kubernetes_io_hostname="master-1"} 481934
container_fs_writes_total{container_name="nginx-5767",container="nginx-5767",device="pod",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",kubernetes_io_hostname="worker-2"} 64941
container_fs_writes_total{container_name="postgres-7229",container="postgres-7229",device="pod",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",kubernetes_io_hostname="worker-2"} 4240341
container_fs_writes_total{container_name="redis-9216",container="redis-9216",device="pod",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1"} 43126
container_fs_writes_total{container_name="redis-9302",container="redis-9302",device="pod",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",kubernetes_io_hostname="worker-2"} 28387
container_memory_cache{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",pod_name="nginx-1248",kubernetes_io_hostname="master-1"} 19812173
container_memory_cache{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",pod_name="nginx-5767",kubernetes_io_hostname="worker-2"} 19267702
container_memory_cache{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",pod_name="postgres-7229",kubernetes_io_hostname="worker-2"} 204010946
container_memory_cache{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 97497227
container_memory_cache{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",pod_name="redis-9302",kubernetes_io_hostname="worker-2"} 119339680
container_memory_failures_total{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",pod_name="nginx-1248",kubernetes_io_hostname="master-1"} 0
container_memory_failures_total{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",pod_name="nginx-5767",kubernetes_io_hostname="worker-2"} 0
container_memory_failures_total{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",pod_name="postgres-7229",kubernetes_io_hostname="worker-2"} 0
container_memory_failures_total{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 0
container_memory_failures_total{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",pod_name="redis-9302",kubernetes_io_hostname="worker-2"} 0
container_memory_mapped_file{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",pod_name="nginx-1248",kubernetes_io_hostname="master-1"} 4953043
container_memory_mapped_file{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",pod_name="nginx-5767",kubernetes_io_hostname="worker-2"} 4816925
container_memory_mapped_file{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",pod_name="postgres-7229",kubernetes_io_hostname="worker-2"} 51002736
container_memory_mapped_file{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 24374306
container_memory_mapped_file{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",pod_name="redis-9302",kubernetes_io_hostname="worker-2"} 29834920
container_memory_max_usage_bytes{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",pod_name="nginx-1248",kubernetes_io_hostname="master-1"} 108966951
container_memory_max_usage_bytes{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",pod_name="nginx-5767",kubernetes_io_hostname="worker-2"} 105972365
container_memory_max_usage_bytes{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",pod_name="postgres-7229",kubernetes_io_hostname="worker-2"} 1122060206
container_memory_max_usage_bytes{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 536234753
container_memory_max_usage_bytes{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",pod_name="redis-9302",kubernetes_io_hostname="worker-2"} 656368242
container_memory_rss{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",pod_name="nginx-1248",kubernetes_io_hostname="master-1"} 79248692
container_memory_rss{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",pod_name="nginx-5767",kubernetes_io_hostname="worker-2"} 77070810
container_memory_rss{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",pod_name="postgres-7229",kubernetes_io_hostname="worker-2"} 816043786
container_memory_rss{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 389988911
container_memory_rss{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",pod_name="redis-9302",kubernetes_io_hostname="worker-2"} 477358721
container_memory_swap{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",pod_name="nginx-1248",kubernetes_io_hostname="master-1"} 0
container_memory_swap{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",pod_name="nginx-5767",kubernetes_io_hostname="worker-2"} 0
container_memory_swap{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",pod_name="postgres-7229",kubernetes_io_hostname="worker-2"} 0
container_memory_swap{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 0
container_memory_swap{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",pod_name="redis-9302",kubernetes_io_hostname="worker-2"} 0
container_memory_usage_bytes{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",pod_name="nginx-1248",kubernetes_io_hostname="master-1"} 99060865
container_memory_usage_bytes{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",pod_name="nginx-5767",kubernetes_io_hostname="worker-2"} 96338513
container_memory_usage_bytes{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",pod_name="postgres-7229",kubernetes_io_hostname="worker-2"} 1020054732
container_memory_usage_bytes{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 487486139
container_memory_usage_bytes{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",pod_name="redis-9302",kubernetes_io_hostname="worker-2"} 596698401
container_memory_working_set_bytes{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",pod_name="nginx-1248",kubernetes_io_hostname="master-1"} 89154778
container_memory_working_set_bytes{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",pod_name="nginx-5767",kubernetes_io_hostname="worker-2"} 86704662
container_memory_working_set_bytes{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",pod_name="postgres-7229",kubernetes_io_hostname="worker-2"} 918049259
container_memory_working_set_bytes{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 438737525
container_memory_working_set_bytes{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",pod_name="redis-9302",kubernetes_io_hostname="worker-2"} 537028561
container_network_receive_bytes_rate{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",kubernetes_io_hostname="master-1",interface="eth0"} 1352558.4197154632
container_network_receive_bytes_rate{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",kubernetes_io_hostname="worker-2",interface="eth0"} 1004761.8042031778
container_network_receive_bytes_rate{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",kubernetes_io_hostname="worker-2",interface="eth0"} 451701.694263443
container_network_receive_bytes_rate{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1",interface="eth0"} 1456917.0647555871
container_network_receive_bytes_rate{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",kubernetes_io_hostname="worker-2",interface="eth0"} 1472484.7102511812
container_network_receive_bytes_total{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",kubernetes_io_hostname="master-1",interface="eth0"} 49061352094
container_network_receive_bytes_total{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",kubernetes_io_hostname="worker-2",interface="eth0"} 4719366686
container_network_receive_bytes_total{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",kubernetes_io_hostname="worker-2",interface="eth0"} 28801403585
container_network_receive_bytes_total{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1",interface="eth0"} 22220899529
container_network_receive_bytes_total{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",kubernetes_io_hostname="worker-2",interface="eth0"} 17703684490
container_network_receive_errors_total{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",kubernetes_io_hostname="master-1",interface="eth0"} 0
container_network_receive_errors_total{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",kubernetes_io_hostname="worker-2",interface="eth0"} 0
container_network_receive_errors_total{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",kubernetes_io_hostname="worker-2",interface="eth0"} 0
container_network_receive_errors_total{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1",interface="eth0"} 0
container_network_receive_errors_total{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",kubernetes_io_hostname="worker-2",interface="eth0"} 0
container_network_receive_packets_dropped_total{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",kubernetes_io_hostname="master-1",interface="eth0"} 327075
container_network_receive_packets_dropped_total{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",kubernetes_io_hostname="worker-2",interface="eth0"} 31462
container_network_receive_packets_dropped_total{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",kubernetes_io_hostname="worker-2",interface="eth0"} 192009
container_network_receive_packets_dropped_total{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1",interface="eth0"} 148139
container_network_receive_packets_dropped_total{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",kubernetes_io_hostname="worker-2",interface="eth0"} 118024
container_network_receive_packets_total{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",kubernetes_io_hostname="master-1",interface="eth0"} 32707568
container_network_receive_packets_total{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",kubernetes_io_hostname="worker-2",interface="eth0"} 3146244
container_network_receive_packets_total{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",kubernetes_io_hostname="worker-2",interface="eth0"} 19200935
container_network_receive_packets_total{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1",interface="eth0"} 14813933
container_network_receive_packets_total{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",kubernetes_io_hostname="worker-2",interface="eth0"} 11802456
container_network_tcp_usage_total{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",kubernetes_io_hostname="master-1",interface="eth0"} 34342946469
container_network_tcp_usage_total{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",kubernetes_io_hostname="worker-2",interface="eth0"} 3303556681
container_network_tcp_usage_total{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",kubernetes_io_hostname="worker-2",interface="eth0"} 20160982511
container_network_tcp_usage_total{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1",interface="eth0"} 15554629677
container_network_tcp_usage_total{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",kubernetes_io_hostname="worker-2",interface="eth0"} 12392579147
container_network_total_bytes_rate{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",kubernetes_io_hostname="master-1",interface="eth0"} 7107684.4796193885
container_network_total_bytes_rate{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",kubernetes_io_hostname="worker-2",interface="eth0"} 4857252.940097781
container_network_total_bytes_rate{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",kubernetes_io_hostname="worker-2",interface="eth0"} 898533.2408917234
container_network_total_bytes_rate{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1",interface="eth0"} 2175752.845834955
container_network_total_bytes_rate{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",kubernetes_io_hostname="worker-2",interface="eth0"} 2440153.0872775023
container_network_transmit_bytes_rate{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",kubernetes_io_hostname="master-1",interface="eth0"} 5755126.059903925
container_network_transmit_bytes_rate{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",kubernetes_io_hostname="worker-2",interface="eth0"} 3852491.1358946036
container_network_transmit_bytes_rate{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",kubernetes_io_hostname="worker-2",interface="eth0"} 446831.5466282804
container_network_transmit_bytes_rate{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1",interface="eth0"} 718835.781079368
container_network_transmit_bytes_rate{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",kubernetes_io_hostname="worker-2",interface="eth0"} 967668.3770263213
container_network_transmit_bytes_total{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",kubernetes_io_hostname="master-1",interface="eth0"} 208755689856
container_network_transmit_bytes_total{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",kubernetes_io_hostname="worker-2",interface="eth0"} 18095152751
container_network_transmit_bytes_total{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",kubernetes_io_hostname="worker-2",interface="eth0"} 28490873230
container_network_transmit_bytes_total{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1",interface="eth0"} 10963683559
container_network_transmit_bytes_total{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",kubernetes_io_hostname="worker-2",interface="eth0"} 11634277435
container_network_transmit_errors_total{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",kubernetes_io_hostname="master-1",interface="eth0"} 0
container_network_transmit_errors_total{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",kubernetes_io_hostname="worker-2",interface="eth0"} 0
container_network_transmit_errors_total{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",kubernetes_io_hostname="worker-2",interface="eth0"} 0
container_network_transmit_errors_total{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1",interface="eth0"} 0
container_network_transmit_errors_total{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",kubernetes_io_hostname="worker-2",interface="eth0"} 0
container_network_transmit_packets_dropped_total{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",kubernetes_io_hostname="master-1",interface="eth0"} 695852
container_network_transmit_packets_dropped_total{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",kubernetes_io_hostname="worker-2",interface="eth0"} 60317
container_network_transmit_packets_dropped_total{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",kubernetes_io_hostname="worker-2",interface="eth0"} 94969
container_network_transmit_packets_dropped_total{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1",interface="eth0"} 36545
container_network_transmit_packets_dropped_total{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",kubernetes_io_hostname="worker-2",interface="eth0"} 38780
container_network_transmit_packets_total{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",kubernetes_io_hostname="master-1",interface="eth0"} 139170459
container_network_transmit_packets_total{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",kubernetes_io_hostname="worker-2",interface="eth0"} 12063435
container_network_transmit_packets_total{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",kubernetes_io_hostname="worker-2",interface="eth0"} 18993915
container_network_transmit_packets_total{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1",interface="eth0"} 7309122
container_network_transmit_packets_total{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",kubernetes_io_hostname="worker-2",interface="eth0"} 7756184
container_network_udp_usage_total{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",kubernetes_io_hostname="master-1",interface="eth0"} 14718405630
container_network_udp_usage_total{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",kubernetes_io_hostname="worker-2",interface="eth0"} 1415810006
container_network_udp_usage_total{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",kubernetes_io_hostname="worker-2",interface="eth0"} 8640421076
container_network_udp_usage_total{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1",interface="eth0"} 6666269861
container_network_udp_usage_total{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",kubernetes_io_hostname="worker-2",interface="eth0"} 5311105349
container_processes{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",pod_name="nginx-1248",kubernetes_io_hostname="master-1"} 7
container_processes{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",pod_name="nginx-5767",kubernetes_io_hostname="worker-2"} 15
container_processes{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",pod_name="postgres-7229",kubernetes_io_hostname="worker-2"} 14
container_processes{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 18
container_processes{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",pod_name="redis-9302",kubernetes_io_hostname="worker-2"} 15
container_start_time_seconds{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",pod_name="nginx-1248",kubernetes_io_hostname="master-1"} 1741778995.6956015
container_start_time_seconds{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",pod_name="nginx-5767",kubernetes_io_hostname="worker-2"} 1741810571.6956418
container_start_time_seconds{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",pod_name="postgres-7229",kubernetes_io_hostname="worker-2"} 1741751506.6955574
container_start_time_seconds{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 1741800016.6954992
container_start_time_seconds{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",pod_name="redis-9302",kubernetes_io_hostname="worker-2"} 1741803245.6956894
container_threads{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",pod_name="nginx-1248",kubernetes_io_hostname="master-1"} 21
container_threads{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",pod_name="nginx-5767",kubernetes_io_hostname="worker-2"} 75
container_threads{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",pod_name="postgres-7229",kubernetes_io_hostname="worker-2"} 28
container_threads{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 90
container_threads{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",pod_name="redis-9302",kubernetes_io_hostname="worker-2"} 75
container_uptime_seconds{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",pod_name="nginx-1248",kubernetes_io_hostname="master-1"} 36273.000410318375
container_uptime_seconds{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",pod_name="nginx-5767",kubernetes_io_hostname="worker-2"} 4697.000501394272
container_uptime_seconds{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",pod_name="postgres-7229",kubernetes_io_hostname="worker-2"} 63762.00035858154
container_uptime_seconds{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 15252.000331163406
container_uptime_seconds{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",pod_name="redis-9302",kubernetes_io_hostname="worker-2"} 12023.000565290451
```

### kube

```
kube_node_status_allocatable{node="master-1",kubernetes_io_hostname="master-1"}{resource="cpu"} 7.2
kube_node_status_allocatable{node="master-1",kubernetes_io_hostname="master-1"}{resource="memory"} 15461882265.6
kube_node_status_allocatable{node="worker-1",kubernetes_io_hostname="worker-1"}{resource="cpu"} 7.2
kube_node_status_allocatable{node="worker-1",kubernetes_io_hostname="worker-1"}{resource="memory"} 15461882265.6
kube_node_status_allocatable{node="worker-2",kubernetes_io_hostname="worker-2"}{resource="cpu"} 7.2
kube_node_status_allocatable{node="worker-2",kubernetes_io_hostname="worker-2"}{resource="memory"} 15461882265.6
kube_node_status_capacity{node="master-1",kubernetes_io_hostname="master-1"}{resource="cpu"} 8.0
kube_node_status_capacity{node="master-1",kubernetes_io_hostname="master-1"}{resource="memory"} 17179869184
kube_node_status_capacity{node="worker-1",kubernetes_io_hostname="worker-1"}{resource="cpu"} 8.0
kube_node_status_capacity{node="worker-1",kubernetes_io_hostname="worker-1"}{resource="memory"} 17179869184
kube_node_status_capacity{node="worker-2",kubernetes_io_hostname="worker-2"}{resource="cpu"} 8.0
kube_node_status_capacity{node="worker-2",kubernetes_io_hostname="worker-2"}{resource="memory"} 17179869184
kube_node_status_condition{node="master-1",kubernetes_io_hostname="master-1"}{condition="DiskPressure",status="false"} 1
kube_node_status_condition{node="master-1",kubernetes_io_hostname="master-1"}{condition="MemoryPressure",status="false"} 1
kube_node_status_condition{node="master-1",kubernetes_io_hostname="master-1"}{condition="NetworkUnavailable",status="false"} 1
kube_node_status_condition{node="master-1",kubernetes_io_hostname="master-1"}{condition="PIDPressure",status="false"} 1
kube_node_status_condition{node="master-1",kubernetes_io_hostname="master-1"}{condition="Ready",status="true"} 1
kube_node_status_condition{node="worker-1",kubernetes_io_hostname="worker-1"}{condition="DiskPressure",status="false"} 1
kube_node_status_condition{node="worker-1",kubernetes_io_hostname="worker-1"}{condition="MemoryPressure",status="false"} 1
kube_node_status_condition{node="worker-1",kubernetes_io_hostname="worker-1"}{condition="NetworkUnavailable",status="false"} 1
kube_node_status_condition{node="worker-1",kubernetes_io_hostname="worker-1"}{condition="PIDPressure",status="false"} 1
kube_node_status_condition{node="worker-1",kubernetes_io_hostname="worker-1"}{condition="Ready",status="true"} 1
kube_node_status_condition{node="worker-2",kubernetes_io_hostname="worker-2"}{condition="DiskPressure",status="false"} 1
kube_node_status_condition{node="worker-2",kubernetes_io_hostname="worker-2"}{condition="MemoryPressure",status="false"} 1
kube_node_status_condition{node="worker-2",kubernetes_io_hostname="worker-2"}{condition="NetworkUnavailable",status="false"} 1
kube_node_status_condition{node="worker-2",kubernetes_io_hostname="worker-2"}{condition="PIDPressure",status="false"} 1
kube_node_status_condition{node="worker-2",kubernetes_io_hostname="worker-2"}{condition="Ready",status="true"} 1
kube_pod_container_resource_limits{container="nginx-1248",namespace="app",pod="nginx-1248",node="master-1"}{resource="cpu"} 2.0
kube_pod_container_resource_limits{container="nginx-1248",namespace="app",pod="nginx-1248",node="master-1"}{resource="memory"} 4294967296
kube_pod_container_resource_limits{container="nginx-5767",namespace="app",pod="nginx-5767",node="worker-2"}{resource="cpu"} 4.0
kube_pod_container_resource_limits{container="nginx-5767",namespace="app",pod="nginx-5767",node="worker-2"}{resource="memory"} 2147483648
kube_pod_container_resource_limits{container="postgres-7229",namespace="monitoring",pod="postgres-7229",node="worker-2"}{resource="cpu"} 2.0
kube_pod_container_resource_limits{container="postgres-7229",namespace="monitoring",pod="postgres-7229",node="worker-2"}{resource="memory"} 1073741824
kube_pod_container_resource_limits{container="redis-9216",namespace="kube-system",pod="redis-9216",node="worker-1"}{resource="cpu"} 2.0
kube_pod_container_resource_limits{container="redis-9216",namespace="kube-system",pod="redis-9216",node="worker-1"}{resource="memory"} 536870912
kube_pod_container_resource_limits{container="redis-9302",namespace="app",pod="redis-9302",node="worker-2"}{resource="cpu"} 0.5
kube_pod_container_resource_limits{container="redis-9302",namespace="app",pod="redis-9302",node="worker-2"}{resource="memory"} 1073741824
kube_pod_container_resource_requests{container="nginx-1248",namespace="app",pod="nginx-1248",node="master-1"}{resource="cpu"} 1.4
kube_pod_container_resource_requests{container="nginx-1248",namespace="app",pod="nginx-1248",node="master-1"}{resource="memory"} 3006477107
kube_pod_container_resource_requests{container="nginx-5767",namespace="app",pod="nginx-5767",node="worker-2"}{resource="cpu"} 2.8
kube_pod_container_resource_requests{container="nginx-5767",namespace="app",pod="nginx-5767",node="worker-2"}{resource="memory"} 1503238553
kube_pod_container_resource_requests{container="postgres-7229",namespace="monitoring",pod="postgres-7229",node="worker-2"}{resource="cpu"} 1.4
kube_pod_container_resource_requests{container="postgres-7229",namespace="monitoring",pod="postgres-7229",node="worker-2"}{resource="memory"} 751619276
kube_pod_container_resource_requests{container="redis-9216",namespace="kube-system",pod="redis-9216",node="worker-1"}{resource="cpu"} 1.4
kube_pod_container_resource_requests{container="redis-9216",namespace="kube-system",pod="redis-9216",node="worker-1"}{resource="memory"} 375809638
kube_pod_container_resource_requests{container="redis-9302",namespace="app",pod="redis-9302",node="worker-2"}{resource="cpu"} 0.35
kube_pod_container_resource_requests{container="redis-9302",namespace="app",pod="redis-9302",node="worker-2"}{resource="memory"} 751619276
kube_pod_container_resource_usage{container="nginx-1248",namespace="app",pod="nginx-1248",node="master-1"}{resource="cpu"} 0.09714432274045035
kube_pod_container_resource_usage{container="nginx-1248",namespace="app",pod="nginx-1248",node="master-1"}{resource="memory"} 99060865
kube_pod_container_resource_usage{container="nginx-5767",namespace="app",pod="nginx-5767",node="worker-2"}{resource="cpu"} 0.18291500505956465
kube_pod_container_resource_usage{container="nginx-5767",namespace="app",pod="nginx-5767",node="worker-2"}{resource="memory"} 96338513
kube_pod_container_resource_usage{container="postgres-7229",namespace="monitoring",pod="postgres-7229",node="worker-2"}{resource="cpu"} 0.38543510161654265
kube_pod_container_resource_usage{container="postgres-7229",namespace="monitoring",pod="postgres-7229",node="worker-2"}{resource="memory"} 1020054732
kube_pod_container_resource_usage{container="redis-9216",namespace="kube-system",pod="redis-9216",node="worker-1"}{resource="cpu"} 0.19035197555475056
kube_pod_container_resource_usage{container="redis-9216",namespace="kube-system",pod="redis-9216",node="worker-1"}{resource="memory"} 487486139
kube_pod_container_resource_usage{container="redis-9302",namespace="app",pod="redis-9302",node="worker-2"}{resource="cpu"} 0.02502383419809137
kube_pod_container_resource_usage{container="redis-9302",namespace="app",pod="redis-9302",node="worker-2"}{resource="memory"} 596698401
kube_pod_container_status_ready{container="nginx-1248",namespace="app",pod="nginx-1248",node="master-1"} 1
kube_pod_container_status_ready{container="nginx-5767",namespace="app",pod="nginx-5767",node="worker-2"} 1
kube_pod_container_status_ready{container="postgres-7229",namespace="monitoring",pod="postgres-7229",node="worker-2"} 1
kube_pod_container_status_ready{container="redis-9216",namespace="kube-system",pod="redis-9216",node="worker-1"} 1
kube_pod_container_status_ready{container="redis-9302",namespace="app",pod="redis-9302",node="worker-2"} 1
kube_pod_container_status_restarts_total{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",pod_name="nginx-1248",kubernetes_io_hostname="master-1"} 0
kube_pod_container_status_restarts_total{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",pod_name="nginx-5767",kubernetes_io_hostname="worker-2"} 0
kube_pod_container_status_restarts_total{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",pod_name="postgres-7229",kubernetes_io_hostname="worker-2"} 0
kube_pod_container_status_restarts_total{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 0
kube_pod_container_status_restarts_total{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",pod_name="redis-9302",kubernetes_io_hostname="worker-2"} 0
kube_pod_container_status_running{container_name="nginx-1248",container="nginx-1248",id="/docker/pod-288348",image="nginx:latest",name="nginx-1248",namespace="app",pod="nginx-1248",pod_name="nginx-1248",kubernetes_io_hostname="master-1"} 1
kube_pod_container_status_running{container_name="nginx-5767",container="nginx-5767",id="/docker/pod-378560",image="nginx:latest",name="nginx-5767",namespace="app",pod="nginx-5767",pod_name="nginx-5767",kubernetes_io_hostname="worker-2"} 1
kube_pod_container_status_running{container_name="postgres-7229",container="postgres-7229",id="/docker/pod-476233",image="postgres:13",name="postgres-7229",namespace="monitoring",pod="postgres-7229",pod_name="postgres-7229",kubernetes_io_hostname="worker-2"} 1
kube_pod_container_status_running{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 1
kube_pod_container_status_running{container_name="redis-9302",container="redis-9302",id="/docker/pod-889207",image="redis:6",name="redis-9302",namespace="app",pod="redis-9302",pod_name="redis-9302",kubernetes_io_hostname="worker-2"} 1
kube_pod_status_phase{container="nginx-1248",namespace="app",pod="nginx-1248",node="master-1"}{phase="Failed"} 0
kube_pod_status_phase{container="nginx-1248",namespace="app",pod="nginx-1248",node="master-1"}{phase="Pending"} 0
kube_pod_status_phase{container="nginx-1248",namespace="app",pod="nginx-1248",node="master-1"}{phase="Running"} 1
kube_pod_status_phase{container="nginx-1248",namespace="app",pod="nginx-1248",node="master-1"}{phase="Succeeded"} 0
kube_pod_status_phase{container="nginx-1248",namespace="app",pod="nginx-1248",node="master-1"}{phase="Unknown"} 0
kube_pod_status_phase{container="nginx-5767",namespace="app",pod="nginx-5767",node="worker-2"}{phase="Failed"} 0
kube_pod_status_phase{container="nginx-5767",namespace="app",pod="nginx-5767",node="worker-2"}{phase="Pending"} 0
kube_pod_status_phase{container="nginx-5767",namespace="app",pod="nginx-5767",node="worker-2"}{phase="Running"} 1
kube_pod_status_phase{container="nginx-5767",namespace="app",pod="nginx-5767",node="worker-2"}{phase="Succeeded"} 0
kube_pod_status_phase{container="nginx-5767",namespace="app",pod="nginx-5767",node="worker-2"}{phase="Unknown"} 0
kube_pod_status_phase{container="postgres-7229",namespace="monitoring",pod="postgres-7229",node="worker-2"}{phase="Failed"} 0
kube_pod_status_phase{container="postgres-7229",namespace="monitoring",pod="postgres-7229",node="worker-2"}{phase="Pending"} 0
kube_pod_status_phase{container="postgres-7229",namespace="monitoring",pod="postgres-7229",node="worker-2"}{phase="Running"} 1
kube_pod_status_phase{container="postgres-7229",namespace="monitoring",pod="postgres-7229",node="worker-2"}{phase="Succeeded"} 0
kube_pod_status_phase{container="postgres-7229",namespace="monitoring",pod="postgres-7229",node="worker-2"}{phase="Unknown"} 0
kube_pod_status_phase{container="redis-9216",namespace="kube-system",pod="redis-9216",node="worker-1"}{phase="Failed"} 0
kube_pod_status_phase{container="redis-9216",namespace="kube-system",pod="redis-9216",node="worker-1"}{phase="Pending"} 0
kube_pod_status_phase{container="redis-9216",namespace="kube-system",pod="redis-9216",node="worker-1"}{phase="Running"} 1
kube_pod_status_phase{container="redis-9216",namespace="kube-system",pod="redis-9216",node="worker-1"}{phase="Succeeded"} 0
kube_pod_status_phase{container="redis-9216",namespace="kube-system",pod="redis-9216",node="worker-1"}{phase="Unknown"} 0
kube_pod_status_phase{container="redis-9302",namespace="app",pod="redis-9302",node="worker-2"}{phase="Failed"} 0
kube_pod_status_phase{container="redis-9302",namespace="app",pod="redis-9302",node="worker-2"}{phase="Pending"} 0
kube_pod_status_phase{container="redis-9302",namespace="app",pod="redis-9302",node="worker-2"}{phase="Running"} 1
kube_pod_status_phase{container="redis-9302",namespace="app",pod="redis-9302",node="worker-2"}{phase="Succeeded"} 0
kube_pod_status_phase{container="redis-9302",namespace="app",pod="redis-9302",node="worker-2"}{phase="Unknown"} 0
```

## Sample Metrics for a Pod

Sample metrics for pod: `redis-9216` in namespace: `kube-system` on node: `worker-1`

```

# CONTAINER_CPU METRICS:
container_cpu_cfs_periods_total{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 152520 = N/A
container_cpu_cfs_throttled_periods_total{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 19 = N/A
container_cpu_load_average_10s{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 0.20938717311022564 = N/A

# CONTAINER_MEMORY METRICS:
container_memory_cache{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 97497227 = N/A
container_memory_failures_total{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 0 = N/A
container_memory_mapped_file{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",pod_name="redis-9216",kubernetes_io_hostname="worker-1"} 24374306 = N/A

# CONTAINER_FS METRICS:
container_fs_io_current{container_name="redis-9216",container="redis-9216",device="pod",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1"} 0 = N/A
container_fs_io_time_seconds_total{container_name="redis-9216",container="redis-9216",device="pod",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1"} 103.3195235781757 = N/A
container_fs_limit_bytes{container_name="redis-9216",container="redis-9216",device="pod",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1"} 10737418240 = N/A

# CONTAINER_NETWORK METRICS:
container_network_receive_bytes_rate{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1",interface="eth0"} 1456917.0647555871 = N/A
container_network_receive_bytes_total{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1",interface="eth0"} 22220900707 = N/A
container_network_receive_errors_total{container_name="redis-9216",container="redis-9216",id="/docker/pod-469940",image="redis:6",name="redis-9216",namespace="kube-system",pod="redis-9216",kubernetes_io_hostname="worker-1",interface="eth0"} 0 = N/A
```

## Example PromQL Queries

These queries can be used in Grafana to visualize the simulator data:

### CPU Usage (Top 10)
```
topk(10, rate(container_cpu_usage_seconds_total{container_name!="POD"}[5m]))
```

### Memory Usage (Top 10)
```
topk(10, container_memory_usage_bytes{container_name!="POD"})
```

### Network Receive Bandwidth (Top 10, in Mbps)
```
topk(10, rate(container_network_receive_bytes_total{container_name!="POD"}[5m]) * 8 / 1000000)
```

### Network Transmit Bandwidth (Top 10, in Mbps)
```
topk(10, rate(container_network_transmit_bytes_total{container_name!="POD"}[5m]) * 8 / 1000000)
```

