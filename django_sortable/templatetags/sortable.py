from django import template
from django.conf import settings


register = template.Library()


SORT_ASC_CLASS = getattr(settings, 'SORT_ASC_CLASS' , 'sort-asc')
SORT_DESC_CLASS = getattr(settings, 'SORT_DESC_CLASS' , 'sort-desc')
SORT_NONE_CLASS = getattr(settings, 'SORT_DESC_CLASS' , 'sort-none')

directions = {
  'asc': {'class': SORT_ASC_CLASS, 'inverse': 'desc'}, 
  'desc': {'class': SORT_DESC_CLASS, 'inverse': 'asc'}, 
}


def parse_tag_token(token):
  """Parses a tag that's supposed to be in this format: {% sortable_link field title %}  """
  bits = [b.strip('"\'') for b in token.split_contents()]
  if len(bits) < 2:
    raise TemplateSyntaxError, "anchor tag takes at least 1 argument"
  try:
    title = bits[2]
  except IndexError:
    if bits[1].startswith(('+', '-')):
      title = bits[1][1:].capitalize()
    else:
      title = bits[1].capitalize()
  try:
    # TODO: make other url checks
    img_url = bits[3]
  except IndexError:
    img_url = None
  
  return (bits[1].strip(), title.strip(), img_url)
  

class SortableLinkNode(template.Node):
  """Build sortable link based on query params."""
  
  def __init__(self, field_name, title, img_url=None):
    if field_name.startswith('-'):
      self.field_name = field_name[1:]
      self.default_direction = 'desc'
    elif field_name.startswith('+'):
      self.field_name = field_name[1:]
      self.default_direction = 'asc'
    else:
      self.field_name = field_name
      self.default_direction = 'asc'
    if img_url:
      self.img_url = template.Variable(img_url)
    self.title = template.Variable(title)
  
  
  def build_link(self, context):
    """Prepare link for rendering based on context."""
    get_params = context['request'].GET.copy()

    field_name = get_params.get('sort', None)
    if field_name:
      del(get_params['sort'])

    direction = get_params.get('dir', None)
    if direction:
      del(get_params['dir'])

    direction = direction if direction in ('asc', 'desc') else 'asc'
    is_current = self.field_name == field_name

    # This part never executes.
    # if is current field, and sort isn't defined, assume asc otherwise desc
    direction = direction or ((self.field_name == field_name) and 'asc' or 'desc')
    
    # if current field and it's sorted, make link inverse, otherwise defalut to asc
    if is_current:
      get_params['dir'] = directions[direction]['inverse']
    else:
      get_params['dir'] = self.default_direction
    
    if is_current:
      css_class = directions[direction]['class']
    else:
      css_class = SORT_NONE_CLASS
    
    params = "&%s" % (get_params.urlencode(),) if len(get_params.keys()) > 0 else ''
    url = ('%s?sort=%s%s' % (context['request'].path, self.field_name, params)).replace('&', '&amp;')
    
    return (url, css_class, is_current)


  def render(self, context):
    url, css_class, is_current = self.build_link(context)
    try:
        title = self.title.resolve(context)
    except template.VariableDoesNotExist:
        title = str(self.title.var)
    return '<a href="%s" class="%s" title="%s">%s</a>' % (url, css_class, title, title)


class SortableTableHeaderNode(SortableLinkNode):
  """Build sortable link header based on query params."""

  def render(self, context):
    url, css_class, is_current = self.build_link(context)
    try:
      title = self.title.resolve(context)
    except template.VariableDoesNotExist:
      title = str(self.title.var)
    try:
      img_url = self.img_url.resolve(context)
    except:
      # raise error if url is invalid?
      img_url = 'None'
    if is_current and img_url is not None:
      is_ascending = css_class == directions['asc']['class']
      rotation_style = ' style="transform: rotate(180deg);"' if is_ascending else ''
      image_class_name = 'sort-img %s-img' % css_class
      direction_image = '<span class="pull-right"><img class="%s" src="%s"%s></span>' % \
                        (image_class_name, img_url, rotation_style)
    else:
      direction_image = ''

    return '<th class="%s"><a href="%s" title="%s">%s</a>%s</th>' % (css_class, url, title, title, direction_image)


class SortableURLNode(SortableLinkNode):
  """Build sortable link header based on query params."""
  
  def render(self, context):
    url, css_class, is_current = self.build_link(context)
    return url


class SortableClassNode(SortableLinkNode):
  """Build sortable link header based on query params."""
  
  def render(self, context):
    url, css_class, is_current = self.build_link(context)
    return css_class


def sortable_link(parser, token):
  field, title, img_url = parse_tag_token(token)
  return SortableLinkNode(field, title)


def sortable_header(parser, token):
  field, title, img_url = parse_tag_token(token)
  return SortableTableHeaderNode(field, title, img_url)


def sortable_url(parser, token):
  field, title, img_url = parse_tag_token(token)
  return SortableURLNode(field, title)


def sortable_class(parser, token):
  field, title, img_url = parse_tag_token(token)
  return SortableClassNode(field, title)

  
sortable_link = register.tag(sortable_link)
sortable_header = register.tag(sortable_header)
sortable_url = register.tag(sortable_url)
sortable_class = register.tag(sortable_class)

