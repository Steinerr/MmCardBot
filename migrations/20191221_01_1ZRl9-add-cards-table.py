"""
add cards table
"""

from yoyo import step

__depends__ = {}

steps = [
    step(
        """
        CREATE TABLE cards (
            id SERIAL PRIMARY KEY NOT NULL,
            user_id INTEGER NOT NULL,
            phrase TEXT NOT NULL,
            translate TEXT NOT NULL,
            created timestamp NOT NULL DEFAULT NOW()
        );
        """
    ),
]
