package system

import (
	"net"
	"runtime"

	"github.com/shirou/gopsutil/v3/cpu"
	"github.com/shirou/gopsutil/v3/load"
	"github.com/shirou/gopsutil/v3/mem"
)

// Snapshot captures lightweight host metrics for heartbeats.
type Snapshot struct {
	CPUPercent float64
	MemoryMB   float64
	Load1      float64
	IP         string
}

// Collect returns the current host metrics snapshot.
func Collect() Snapshot {
	snap := Snapshot{}
	if values, err := cpu.Percent(0, false); err == nil && len(values) > 0 {
		snap.CPUPercent = values[0]
	}
	if vm, err := mem.VirtualMemory(); err == nil {
		snap.MemoryMB = float64(vm.Used) / (1024 * 1024)
	}
	if avg, err := load.Avg(); err == nil {
		snap.Load1 = avg.Load1
	}
	// Fall back to runtime stats if some collectors are unavailable.
	if snap.MemoryMB == 0 {
		var m runtime.MemStats
		runtime.ReadMemStats(&m)
		snap.MemoryMB = float64(m.Alloc) / (1024 * 1024)
	}
	snap.IP = firstNonLoopbackIP()
	return snap
}

func firstNonLoopbackIP() string {
	addrs, err := net.InterfaceAddrs()
	if err != nil {
		return ""
	}
	for _, addr := range addrs {
		var ip net.IP
		switch v := addr.(type) {
		case *net.IPNet:
			ip = v.IP
		case *net.IPAddr:
			ip = v.IP
		}
		if ip == nil || ip.IsLoopback() {
			continue
		}
		if ipv4 := ip.To4(); ipv4 != nil {
			return ipv4.String()
		}
	}
	return ""
}
