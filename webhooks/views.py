from django.urls import path, include
from webhooks.models import Case
from rest_framework import serializers, viewsets
from django.db.models import Sum,Avg,Min,Max,F
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import models
from django.shortcuts import render
from datetime import datetime,date
from django.utils import timezone

def home_page(request):
    title = "COVID 19- Info"
    return render(request,'index.html', {'title':title})

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ["date", "state", "tcin", "tcfn", "cured", "death"]

class CaseViewSet(viewsets.ModelViewSet):
    
    def get_queryset(self):
        fields = self.request.query_params.getlist('field_name', ['death'])
        queries = self.request.query_params.getlist('query', ['gt'])
        values = self.request.query_params.getlist('value', [148500])
        date_param = self.request.query_params.get('date', None)

        filters = {}

        for field, query, value in zip(fields, queries, values):
            field_key = f"{field}__{query}"
            filters[field_key] = value

        # Process and validate the date parameter
        if date_param:
            try:
                date_param = timezone.datetime.strptime(date_param, '%Y-%m-%d').date()
            except ValueError:
                date_param = None

        # Ensure the date is within the specified range
        if date_param:
            start_date = timezone.datetime(2020, 3, 10).date()
            end_date = timezone.datetime(2023, 4, 29).date()

            date_param = max(start_date, min(date_param, end_date))

            # Add the date filter to the queryset
            filters['date'] = date_param

        queryset = Case.objects.filter(**filters)

        return queryset

    @action(detail=False, methods=['GET'])
    def summary(self, request):
        state = self.request.query_params.get('state', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)

        min_date = datetime.strptime('2020-03-10', '%Y-%m-%d').date()
        max_date = datetime.strptime('2023-04-29', '%Y-%m-%d').date()

        if start_date:
            start_date = max(min_date, min(max_date, datetime.strptime(start_date, '%Y-%m-%d').date()))

        if end_date:
            end_date = max(min_date, min(max_date, datetime.strptime(end_date, '%Y-%m-%d').date()))

        filters = {'state': state}
        if start_date and end_date:
            filters['date__range'] = (start_date, end_date)

        max_death_data = Case.objects.filter(**filters).aggregate(
            max_death=Max('death'),
            date_of_max_death=Max(F('date'), output_field=models.DateField())
        )

        min_death_data = Case.objects.filter(**filters).aggregate(
            min_death=Min('death'),
            date_of_min_death=Min(F('date'), output_field=models.DateField())
        )

        max_cured_data = Case.objects.filter(**filters).aggregate(
            max_cured=Max('cured'),
            date_of_max_cured=Max(F('date'), output_field=models.DateField())
        )

        min_cured_data = Case.objects.filter(**filters).aggregate(
            min_cured=Min('cured'),
            date_of_min_cured=Min(F('date'), output_field=models.DateField())
        )

        summary_data = {
            'max_death': max_death_data['max_death'],
            'date_of_max_death': max_death_data['date_of_max_death'],
            'max_cured': max_cured_data['max_cured'],
            'date_of_max_cured': max_cured_data['date_of_max_cured'],
            'min_death': min_death_data['min_death'],
            'date_of_min_death': min_death_data['date_of_min_death'],
            'min_cured': min_cured_data['min_cured'],
            'date_of_min_cured': min_cured_data['date_of_min_cured'],
            # Add more as needed
        }

        return Response(summary_data)
    
    serializer_class = ClientSerializer