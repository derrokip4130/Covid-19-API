import numpy as np
from webhooks.models import Case
from django.db.models import Sum,Avg,Min,Max,F
from django.db import models
from django.shortcuts import render
from django.utils import timezone
from rest_framework import serializers, viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from datetime import datetime,date
from sklearn.linear_model import LinearRegression
from scipy.optimize import curve_fit

def home_page(request):
    title = "COVID 19- Info"
    return render(request,'index.html', {'title':title})

def logistic_function(x, a, b, c):
    return a / (1 + np.exp(-b * (x - c)))

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

        death_data = Case.objects.filter(**filters).aggregate(
            min_death=Min('death'),
            max_death=Max('death'),
            sum_death=Sum('death'),
            avg_death=Avg('death'),
            date_of_min_death=Min(F('date'), output_field=models.DateField()),
            date_of_max_death=Max(F('date'), output_field=models.DateField())
        )
        cured_data = Case.objects.filter(**filters).aggregate(
            min_cured=Min('cured'),
            max_cured=Max('cured'),
            sum_cured=Sum('cured'),
            avg_cured=Avg('cured'),
            date_of_min_cured=Min(F('date'), output_field=models.DateField()),
            date_of_max_cured=Max(F('date'), output_field=models.DateField())
        )
        tcin_data = Case.objects.filter(**filters).aggregate(
            min_tcin=Min('tcin'),
            max_tcin=Max('tcin'),
            sum_tcin=Sum('tcin'),
            avg_tcin=(Avg('tcin')),
            date_of_min_tcin=Min(F('date'), output_field=models.DateField()),
            date_of_max_tcin=Max(F('date'), output_field=models.DateField())
        )

        death_increase = death_data['max_death'] - death_data['min_death']
        cured_increase = cured_data['max_cured'] - cured_data['min_cured']
        tcin_increase = tcin_data['max_tcin'] - tcin_data['min_tcin']

        death_rate_increase = (death_increase / death_data['min_death']) * 100 if death_data['min_death'] else None
        cured_rate_increase = (cured_increase / cured_data['min_cured']) * 100 if cured_data['min_cured'] else None
        tcin_rate_increase = (tcin_increase / tcin_data['min_tcin']) * 100 if tcin_data['min_tcin'] else None

        cured_data['cured_rate'] = cured_rate_increase
        death_data['death_rate'] = death_rate_increase
        tcin_data['tcin_rate'] = tcin_rate_increase

        cured_data['avg_cured'] = int(cured_data['avg_cured'])
        death_data['avg_death'] = int(death_data['avg_death'])
        tcin_data['avg_tcin'] = int(tcin_data['avg_tcin'])

        summary_data = {
            'cured': cured_data,
            'death': death_data,
            'tcin': tcin_data,
            # Add more as needed
        }

        return Response(summary_data)
    
    def predict_cases(self, request, state, date):
        # Retrieve the dataset for the specified state
        dataset = Case.objects.filter(state=state).values_list('date', 'tcin', 'death', 'cured').order_by('date')

        # Extract dates and variable values
        dates, tcin_values, death_values, cured_values = zip(*dataset)

        # Convert dates to numerical values (e.g., days since the start date)
        start_date = min(dates)
        numerical_dates = [(date - start_date).days for date in dates]

        if datetime.strptime(date, "%Y-%m-%d").date() < datetime.strptime('2023-04-29', '%Y-%m-%d').date():
            date = '2023-04-29'

        # Convert input date to numerical value
        input_date = timezone.datetime.strptime(date, '%Y-%m-%d').date()
        numerical_input_date = (input_date - start_date).days

        # Reshape data for training
        X_train = np.array(numerical_dates).reshape(-1, 1)

        # Train linear regression models for each variable
        models = {}
        variables = ['tcin', 'death', 'cured']

        for variable in variables:
            y_train = np.array(locals()[f'{variable}_values'])

            # Apply decay factor to simulate the expected drop in values
            decay_factor = 0.1  # Adjust this value based on the expected rate of decline
            y_train = y_train * decay_factor

            model = LinearRegression()
            model.fit(X_train, y_train)
            models[variable] = model

        # Predict values for the input date
        predictions = {}
        for variable in variables:
            numerical_input_date_array = np.array([[numerical_input_date]])
            predicted_value = models[variable].predict(numerical_input_date_array)[0]
            predictions[variable] = int(predicted_value)

        return Response(predictions)
    
    serializer_class = ClientSerializer