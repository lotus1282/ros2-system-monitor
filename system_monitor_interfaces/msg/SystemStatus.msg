# Snapshot of host system state.
# All memory values are bytes. Network byte counters are cumulative since boot.
# Rates are computed from the interval between two consecutive samples.

builtin_interfaces/Time stamp

# Hostname reported by the machine that produced this sample.
string hostname

# System-wide CPU utilization, 0.0 - 100.0.
float32 cpu_percent

# Physical memory utilization, 0.0 - 100.0.
float32 memory_percent

# Total physical memory in bytes.
uint64 memory_total

# Used physical memory in bytes.
uint64 memory_used

# Available physical memory in bytes.
uint64 memory_available

# Cumulative bytes received on all network interfaces since boot.
uint64 net_bytes_recv

# Cumulative bytes sent on all network interfaces since boot.
uint64 net_bytes_sent

# Receive rate in bytes per second since the previous sample.
float32 net_recv_rate

# Send rate in bytes per second since the previous sample.
float32 net_send_rate
