import os

from django.core.management.base import BaseCommand

from vehicles import demo_data


class Command(BaseCommand):
    help = "Create a demo dealership, an admin, a customer and a stocked showroom (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--admin-password",
            default=os.environ.get("DEMO_ADMIN_PASSWORD", "Admin@12345"),
            help="Password for admin@dealership.local (default: $DEMO_ADMIN_PASSWORD or Admin@12345).",
        )
        parser.add_argument(
            "--customer-password",
            default=os.environ.get("DEMO_CUSTOMER_PASSWORD", "Customer@12345"),
            help="Password for customer@dealership.local (default: $DEMO_CUSTOMER_PASSWORD or Customer@12345).",
        )

    def handle(self, *args, admin_password, customer_password, **options):
        dealership = demo_data.seed(admin_password=admin_password, customer_password=customer_password)
        self.stdout.write(self.style.SUCCESS(f"Demo data ready for '{dealership.name}'."))
        self.stdout.write(f"  Admin:    {demo_data.ADMIN_EMAIL}")
        self.stdout.write(f"  Customer: {demo_data.CUSTOMER_EMAIL}")
