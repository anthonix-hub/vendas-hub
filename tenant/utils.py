# from django.contrib.auth import get_user_model
# from tenant.models import Tenant, Domain

# User = get_user_model()

# def register_user_and_tenant(email, password, blog_name, subdomain):
#     # Create user
#     user = User.objects.create_user(email=email, password=password)
#     user.save()

#     # Create tenant
#     tenant = Tenant(user=user, blog_name=blog_name)
#     tenant.save()

#     # Create tenant domain
#     domain = Domain(tenant=tenant, domain=f'{subdomain}.localhost', is_primary=True)
#     domain.save()

#     return user, tenant


from tenant.models import Tenant, Domain

def register_user_and_tenant(name, subdomain, email):
    
    print(">>>>>>>>>>>>>> currently in the utils page <<<<<<<<<<<<<<<<<<<<")
    
    print(">>>>>>>>>>>>>> about to register a tenant <<<<<<<<<<<<<<<<<<<<")
    # Create the tenant for the user
    tenant = Tenant.objects.create(
        # user=user,
        name = name,
        schema_name = subdomain,  # Assuming the subdomain will be used as schema name
        email=email,
        # domain_url = 'localhost',
    )

    print(">>>>>>>>>>>>>> about to register a Domain <<<<<<<<<<<<<<<<<<<<")
    # Create the domain for the tenant
    Domain.objects.create(
        tenant=tenant,
        domain=f"{subdomain}.localhost",  # Adjust to your main domain
        is_primary=True
    )

    return tenant
