def open_tickets(request):
    tickets = Ticket.objects.filter(status='Open')
    service_families = ServiceFamily.objects.all()

    # Apply filters
    service_family = request.GET.get('service_family')
    priority = request.GET.get('priority')
    impact = request.GET.get('impact')

    if service_family:
        tickets = tickets.filter(service_family_id=service_family)
    if priority:
        tickets = tickets.filter(priority=priority)
    if impact:
        tickets = tickets.filter(impact=impact)

    context = {
        'tickets': tickets,
        'service_families': service_families,
    }
    return render(request, 'tickets/open_tickets.html', context)

def closed_tickets(request):
    tickets = Ticket.objects.filter(status='Closed')
    service_families = ServiceFamily.objects.all()

    # Apply filters
    service_family = request.GET.get('service_family')
    priority = request.GET.get('priority')
    impact = request.GET.get('impact')

    if service_family:
        tickets = tickets.filter(service_family_id=service_family)
    if priority:
        tickets = tickets.filter(priority=priority)
    if impact:
        tickets = tickets.filter(impact=impact)

    context = {
        'tickets': tickets,
        'service_families': service_families,
    }
    return render(request, 'tickets/closed_tickets.html', context)