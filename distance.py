'''
Created on Dec 9, 2012

@author: woo
'''
import httplib
import math
import string

def distance_on_unit_sphere(lat1, long1, lat2, long2):

    # Convert latitude and longitude to 
    # spherical coordinates in radians.
    degrees_to_radians = math.pi/180.0
        
    # phi = 90 - latitude
    phi1 = (90.0 - lat1)*degrees_to_radians
    phi2 = (90.0 - lat2)*degrees_to_radians
        
    # theta = longitude
    theta1 = long1*degrees_to_radians
    theta2 = long2*degrees_to_radians
        
    # Compute spherical distance from spherical coordinates.
        
    # For two locations in spherical coordinates 
    # (1, theta, phi) and (1, theta, phi)
    # cosine( arc length ) = 
    #    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
    # distance = rho * arc length
    
    cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
           math.cos(phi1)*math.cos(phi2))
    arc = math.acos( cos )

    # Remember to multiply arc by the radius of the earth 
    # in your favorite set of units to get length.
    return arc
def main(hostname):
    conn = httplib.HTTPConnection("www.freegeoip.net")
    request_host = "/xml/"+hostname
    conn.request("GET", request_host)
    r1 = conn.getresponse()
    if r1.status == httplib.OK:
        data1 = r1.read()
        p1=string.find(data1,'<Latitude>')
        p2=string.rfind(data1,'</Latitude>')
        targetlati=float(data1[p1+10:p2])
        
        p1=string.find(data1,'<Longitude>')
        p2=string.rfind(data1,'</Longitude>')
        targetlongi=float(data1[p1+11:p2])
        
        
        
        #print targetlati, targetlongi
        distance = distance_on_unit_sphere(targetlati,targetlongi, 41.5074, -81.6053)
        print hostname, 'distance=',distance*6373,'km'
    
if __name__=="__main__":
    main ('www.google.com')
    main('facebook.com')
    main('blogspot.com')
    main('yandex.ru')
    main('googleusercontent.com')
    main('google.es')
    main('xvideos.com')
    main('youku.com')
    main('cnn.com')
    main('redtube.com')
    main('google.pl')
    main('cnet.com')
