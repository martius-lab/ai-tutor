import reflex as rx
from sqlmodel import select
from aitandem.models import Exercise
from typing import List, Optional

def fetch_exercises(session_id: Optional[str] = None) -> List[Exercise]:
    with rx.session() as session:
        exercises = session.exec(select(Exercise)).all()
        return exercises