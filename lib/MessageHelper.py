import sys
import struct
import socket

import XProtocol
from Utils import flatten, format_length

class MessageHelperException(Exception):
  """General Exception raised by MessageHelper."""
    
  def __init__(self, desc):
    """Construct an exception.

    @param desc: description of an error
    """
    self.desc = desc

  def __str__(self):
    """Return textual representation of an error."""
    return str(self.desc)


class MessageHelper:
  
  def __init__(self, context):
    self.sock = context['socket']
    self.streamid = context['streamid']
  
  def build_request(self, request_struct, params):
    """Return a packed representation of the given params mapped onto
    the given request struct."""    
    if not len(params) == len(request_struct):
      raise MessageHelperException("[!] Error building request: wrong " + \
                                   "number of parameters")
      
    request = tuple()
    format = '>'
    
    for member in request_struct:
      request += (params[member['name']],)
      if member.has_key('size'):
        if member['size'] == 'dlen':
          format += str(params[member['size']]) + member['type']
        else:
          format += str(member['size']) + member['type']
      else: 
        format += member['type']

    request = tuple(flatten(request))
    return struct.pack(format, *request)
    
  def send_request(self, requestid, request):
    """Send a packed request and return a packed response."""
    try:
      self.sock.send(request)
    except socket.error, e:
      raise MessageHelperException('Error sending %s request: %s' 
                                         % (requestid, e))
    try:  
      response = self.sock.recv(4096)
    except socket.error, e:
      raise MessageHelperException('Error receiving %s response: %s' 
                                         % (requestid, e))
    return response    
  
  def unpack_response(self, response, requestid):
    """Return an unpacked tuple representation of a server response."""
    header_struct = self.get_struct('ServerResponseHeader')
    format = '>'
    
    for member in header_struct:
      format += member['type']
    
    dlen = struct.unpack(format + ('s' * (len(response) - 8))
                                      , response)[2]
    
    try:
      body_struct = self.get_struct('ServerResponseBody_' 
                                      + requestid[4:].title())
    except: body_struct = list()
    
    for member in body_struct:
      if member.has_key('size'):
        format += str(member['size']) + member['type']
      else: 
        format += member['type']
        
    if not body_struct:
      format += (str(dlen) + 's')
    
    response = struct.unpack(format, response)
    return self.get_responseid(response[1]), response
    
  def get_struct(self, name):
    """Return a representation of a struct as a list of dicts."""
    if hasattr(XProtocol, name):
        return getattr(XProtocol, name)
    else:
      raise MessageHelperException("[!] XProtocol struct not found: %s" 
                                   % name)
    
  def get_requestid(self, requestid):
    """Return the integer request ID associated with the given string
    request ID.""" 
    if hasattr(XProtocol.XRequestTypes, requestid):
      return getattr(XProtocol.XRequestTypes, requestid)
    else:
      print "[!] Unknown request ID:", requestid
      sys.exit(1)
      
  def get_responseid(self, responseid):
    """Return the string response ID associated with the given integer
    response ID."""
    try:
      respid = XProtocol.XResponseType.reverse_mapping[responseid]
    except KeyError, e:
      print "[!] Unknown response ID:", responseid
      sys.exit(1) 
      
    return respid
