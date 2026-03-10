from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255, blank=True, default='')
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, default='')
    address = models.TextField(blank=True, default='')

    def __str__(self):
        return self.full_name or self.name


class AgentConversation(models.Model):
    """Stores AI agent conversation history per customer."""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation #{self.id} - {self.customer.name}"


class AgentMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('agent', 'Agent'),
    ]
    conversation = models.ForeignKey(AgentConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    intent = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.role}] {self.content[:50]}"

