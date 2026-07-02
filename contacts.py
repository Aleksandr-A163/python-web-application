from dataclasses import dataclass


@dataclass
class Contact:
    contact_id: int
    name: str
    phone: str
    comment: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.contact_id,
            "name": self.name,
            "phone": self.phone,
            "comment": self.comment,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Contact":
        return cls(
            contact_id=int(data["id"]),
            name=str(data["name"]),
            phone=str(data["phone"]),
            comment=str(data.get("comment", "")),
        )
