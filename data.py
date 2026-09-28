from dataclasses import dataclass
from enum import Enum


class ProcessState(Enum):
    ABSENT = "Отсутствует"
    READY = "Готов"
    ACTIVE = "Активен"
    BLOCKED = "Блокирован"

class CPUState(Enum):
    WAITING = "Ожидание"
    WORKING = "Работа"

class CommandType(Enum):
    COMPUTE = "Вычисление"
    IO = "Ввод-вывод"
    EXIT = "Завершение"

@dataclass
class Task:
    task_id: int
    memory_size: int
    command_count: int
    io_percent: int = 0
    io_duration: int = 0
    priority: int = 0


@dataclass
class RSW:
    process_id: int = 0
    task_id: int = 0
    memory_size: int = 0
    command_count: int = 0
    pc: int = 0
    state: ProcessState = ProcessState.ABSENT
    priority: int = 0
    io_remaining: int = 0


@dataclass
class Memory:
    total: int
    used: int = 0

    @property
    def free(self) -> int:
        return self.total - self.used
