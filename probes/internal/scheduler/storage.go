package scheduler

type Storage interface {
	Load() ([]Config, uint64, error)
	Save([]Config, uint64) error
}
