import logging

# ------------------------------------------------------------
# LOGGING CONFIGURATION
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)


class Department:
    def __init__(self, name, budget=0):
        self.name = name
        self.budget = max(budget, 0)
        self.members = []
        logging.info(f"Department created: {self.name} with budget {self.budget}")

    def add_member(self, user):
        """Adds user to this department while preventing duplicates."""
        if user in self.members:
            logging.warning(f"{user.name} is already a member of {self.name}")
            return f"{user.name} is already a member of {self.name}."

        self.members.append(user)
        user.department = self
        logging.info(f"Added {user.name} to {self.name}")
        return f"{user.name} added to {self.name} department."

    def add_budget(self, amount):
        """Increase budget with validation."""
        if amount <= 0:
            logging.error("Attempted to add a non-positive budget amount")
            return "Amount must be positive."

        self.budget += amount
        logging.info(f"{self.name} budget increased by {amount}. New budget: {self.budget}")
        return f"Budget updated. New budget: {self.budget}"

    def deduct_budget(self, amount):
        """Deduct from budget safely."""
        if amount <= 0:
            logging.error("Attempted to deduct a non-positive budget amount")
            return "Amount must be positive."

        if amount > self.budget:
            logging.warning(f"{self.name} has insufficient budget for deduction.")
            return "Not enough budget!"

        self.budget -= amount
        logging.info(f"{self.name} spent {amount}. Remaining: {self.budget}")
        return f"Amount deducted. Remaining budget: {self.budget}"

    def list_members(self):
        """Return list of member info."""
        logging.info(f"Listing members of {self.name}")
        return [(user.name, user.role, user.level) for user in self.members]


class User:
    def __init__(self, name, role, level=1, department=None):
        self.name = name
        self.role = role
        self.level = level
        self.department = department
        logging.info(f"User created: {self.name}, role: {self.role}, level: {self.level}")

        if department is not None:
            department.add_member(self)

    def promote(self):
        self.level += 1
        logging.info(f"{self.name} promoted to level {self.level}")
        return f"{self.name} promoted to level {self.level}."

    def change_role(self, new_role):
        old_role = self.role
        self.role = new_role
        logging.info(f"{self.name} changed role from {old_role} → {new_role}")
        return f"{self.name}'s role changed from {old_role} to {new_role}."

    def assign_department(self, department):
        logging.info(f"Assigning {self.name} to {department.name}")
        return department.add_member(self)


# ---------------------- TEST MODEL ---------------------- #

cs_dept = Department("Computer Science", 50000)
mech_dept = Department("Mechanical Engineering", 30000)

user1 = User("Ananya", "Student")
user2 = User("Harshal", "Student", level=2)

print(user1.assign_department(cs_dept))
print(user2.assign_department(mech_dept))

print(user1.promote())
print(cs_dept.add_budget(10000))
print(mech_dept.deduct_budget(5000))

print("CS Dept Members:", cs_dept.list_members())
print("ME Dept Members:", mech_dept.list_members())
