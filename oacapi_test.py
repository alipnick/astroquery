import astropy.coordinates as coord
# Test region query
import astropy.units as u
from astroquery.oac import OAC

'''# Test object query
photometry = OAC.query_object(object_name='GW170817')
print(photometry[:5])
'''


ra = 197.45037
dec = -23.38148


test_coords = coord.SkyCoord(ra=ra, dec=dec, unit=(u.deg, u.deg))

test_table = OAC.query_region(coordinates=test_coords,
                                 width=10,
                                 height=10,
                                 get_query_payload=False,
                                 verbose=True)

print(test_table[:5])
