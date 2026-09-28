from data import RSW, ProcessState


def scheduler(process_table: list[RSW]) -> int | None:
    ready_processes = [
        rsw
        for rsw in process_table
        if rsw.state == ProcessState.READY
    ]

    if not ready_processes:
        return None

    next_process = max(
        ready_processes,
        key=lambda rsw: rsw.priority,
    )

    return next_process.process_id
