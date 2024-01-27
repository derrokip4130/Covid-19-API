from django.db.models.constraints import UniqueConstraint
from django.db import models
from datetime import datetime

class Case(models.Model):
    date = models.DateField(db_index=True)
    state = models.CharField(max_length=100, db_index=True)
    tcin = models.IntegerField()
    tcfn = models.IntegerField()
    cured = models.IntegerField()
    death = models.IntegerField()

    UniqueConstraint(fields=['date', 'state'], name='unique_state_and_date')
    