from main.models import Cash
from .DateFilterSerializer import DateFilterSerializer


class CashSerializer(DateFilterSerializer):
    def __init__(self, *args, include_children=False, **kwargs):
        self.include_children = include_children
        super().__init__(*args, **kwargs)

    class Meta:
        model = Cash
        fields = ['id', 'name', 'value', 'date',
                  'reference_date', 'income', 'db']
