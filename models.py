from tortoise import fields
from tortoise.models import Model

# Define the Role model
class Role(Model):
    id = fields.IntField(pk=True)
    type = fields.CharField(max_length=50, unique=True)
    # Pre-add roles method
    async def pre_add_roles(cls):
        for role_type in ["secretary", "patient", "doctor"]:
            await Role.get_or_create(type=role_type)

    def __str__(self):
        return self.type

# Define the User model
class User(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True)
    password_hash = fields.CharField(max_length=255)
    role_id = fields.ForeignKeyField('models.Role', related_name='userroles')

    # Validation method for role types
    async def validate_role_type(cls, role_type: str):
        valid_roles = ["secretary", "patient", "doctor"]
        if role_type.lower() not in valid_roles:
            raise ValueError("Invalid role type")

    def __str__(self):
        return self.username

# Define the PatientInfo model
class PatientInfo(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    contact_info = fields.CharField(max_length=255)
    medical_info = fields.TextField()
    assigned_to = fields.ForeignKeyField('models.User', related_name='users')