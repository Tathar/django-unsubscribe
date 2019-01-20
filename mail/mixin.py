from django.views import generic
#from django.views.generic.detail import SingleObjectMixin


class ajaxGetMixin() :
    def get(self, request, *args, **kwargs):
        if request.is_ajax() and "ajax" in request.GET :
            handler = getattr(self, "ajax_%s" % request.GET['ajax'], self.http_method_not_allowed)
            return handler(request, *args, **kwargs)

        return super().get(request, args, kwargs)
    
    
# class ObjectFormMixin(generic.detail.SingleObjectMixin):
#         
#     def get_object(self, queryset=None):
#         """
#         Return the object the view is displaying.
#         Require `self.queryset` and a `pk` or `slug` argument in the URLconf.
#         Subclasses can override this to return any object.
#         """
#         # Use a custom queryset if provided; this is required for subclasses
#         # like DateDetailView
#         if queryset is None:
#             queryset = self.get_queryset()
#         # Next, try looking up by primary key.
#         pk = self.kwargs.get(self.pk_url_kwarg)
#         slug = self.kwargs.get(self.slug_url_kwarg)
#         if pk is not None:
#             queryset = queryset.filter(pk=pk)
#         # Next, try looking up by slug.
#         if slug is not None and (pk is None or self.query_pk_and_slug):
#             slug_field = self.get_slug_field()
#             queryset = queryset.filter(**{slug_field: slug})
#         # If none of those are defined, it's an error.
#         if pk is None and slug is None:
#             return None
#             
#         try:
#             # Get the single item from the filtered queryset
#             obj = queryset.get()
#         except queryset.model.DoesNotExist:
#             raise Http404(_("No %(verbose_name)s found matching the query") %
#                           {'verbose_name': queryset.model._meta.verbose_name})
#         return obj


class ObjectFormView(generic.detail.SingleObjectMixin , generic.FormView):

    def __init__(self, **kwargs):
        """
        Constructor. Called in the URLconf; can contain helpful extra
        keyword arguments, and other things.
        """
        self.object = None
        super().__init__(**kwargs)
        
    def get_object(self, queryset=None):
        """
        Return the object the view is displaying.
        Require `self.queryset` and a `pk` or `slug` argument in the URLconf.
        Subclasses can override this to return any object.
        """
        # Use a custom queryset if provided; this is required for subclasses
        # like DateDetailView
        if queryset is None:
            queryset = self.get_queryset()
        # Next, try looking up by primary key.
        pk = self.kwargs.get(self.pk_url_kwarg)
        slug = self.kwargs.get(self.slug_url_kwarg)
        if pk is not None:
            queryset = queryset.filter(pk=pk)
        # Next, try looking up by slug.
        if slug is not None and (pk is None or self.query_pk_and_slug):
            slug_field = self.get_slug_field()
            queryset = queryset.filter(**{slug_field: slug})
        # If none of those are defined, it's an error.
        if pk is None and slug is None:
            return None
        
        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                          {'verbose_name': queryset.model._meta.verbose_name})
        
        return obj
    
    def get_context_data(self, **kwargs):
        """Insert the single object into the context dict."""
        context = {}
        if self.object:
            context_object_name = self.get_context_object_name(self.object)
            if context_object_name:
                context[context_object_name] = self.object
            else :
                context['object'] = self.object
                
        context.update(kwargs)
        
        return super(generic.FormView, self).get_context_data(**context)
    
    
    def render_to_response(self, context, **response_kwargs):

        if self.model :
            context[self.model.__name__.lower()] = self.object
        
        return super().render_to_response(context, **response_kwargs)
    
