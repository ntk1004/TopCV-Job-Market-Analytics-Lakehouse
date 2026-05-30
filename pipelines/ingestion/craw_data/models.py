from dataclasses import dataclass, asdict


@dataclass(slots=True)
class JobItem:
    title: str
    company: str
    location: str
    salary: str
    skills: str
    job_description: str
    job_url: str
    source_page: int
    experience : str

    def to_dict(self) -> dict:
        return asdict(self)

