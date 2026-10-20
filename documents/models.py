from django.db import models


class InvoiceTemplate(models.Model):
    name = models.CharField(max_length=100)
    code = models.SlugField(max_length=50, unique=True)
    template_path = models.CharField(max_length=255)
    preview_image = models.ImageField(upload_to="documents/invoice_previews/",null=True,blank=True, )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        

