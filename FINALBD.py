import psycopg2
import math
import json
import folium 
import pandas as pd
import os 
import sys




def height_by_divisions(db, grao, points, m, color):
	print('SHOWING MAP BY ' + grao)
	print('SHOWING POINTS FOR ' + points)
	if grao == 'freguesia':
		final_query = 'SELECT count(*), st_AsGeoJSON(geom), freguesia FROM projBD, cont_aad_caop2017 WHERE st_contains(geom,' + points + ') GROUP BY geom,freguesia;'
	else:

		geometry2 = 'st_union(geom) g'
		aux_query5 = 'SELECT ' + grao + ' d, ' + geometry2 + '  FROM cont_aad_caop2017 GROUP BY ' + grao
		final_query = 'SELECT count(*), st_AsGeoJSON(st_boundary(coords.g)), coords.d FROM projBD, (' + aux_query5 + ') coords WHERE st_contains(coords.g,' + points + ') GROUP BY coords.g,coords.d;'
	cursor = db.cursor()
	cursor.execute(final_query)
	results = cursor.fetchall()
	#print(results)
	weights = [int(res[0]) for res in results]
	names = [res[2] for res in results]
	print(weights)
	print(names)
	#regions = [res[1] for res in results]
	col1 = ['Region' + str(i) for i in range(len(results))]
	d = {'ID' : col1 , 'Services' : weights}
	data2 = pd.DataFrame(data=d)
	data2['ID'] = data2['ID'].astype(str)
	data2['Services'] = data2['Services'].astype(int)
	finalJSON = '{"type":"FeatureCollection","features":['
	i = 0
	

	for res in results:
	    #folium.GeoJson(res[1]).add_to(m)
	    if i > 0:
	        finalJSON += ','
	    
	    
	    finalJSON += '{"type":"Feature","properties":{"name":"' + names[i] + '", "id":"Region' + str(i) + '", "style":{"fill":"True"}},"geometry":' + res[1] + '}'
	    i += 1
	finalJSON += ']}'

	#print(finalJSON)
	print('------')
	finalJSON = json.loads(finalJSON)
	#finalJSON2 = finalJSON
	#print(finalJSON["features"][0]["properties"])
	folium.Choropleth(
	    geo_data =finalJSON,
	    data=data2,
	    bins = 8,
	    columns=['ID', 'Services'],
	    key_on= 'feature.properties.id',
	    fill_color= color,
	    legend_name='Taxi Services - ' + points,
	    overlay = True,
	    name = points,
	    show = False,
	    highlight = True
	).add_to(m)



def heat_grid(db,grid_width, grid_height,points,m):
	print('SHOWING MAP BY GRID ' + str(grid_width) + "x" + str(grid_height))
	print('SHOWING POINTS FOR ' + points)
	envelope = 'SELECT st_envelope(st_collect(st_transform(' + points + ',3763))) e FROM projBD'
	corners_query = 'SELECT st_xmin(env.e) xmin , st_ymin(env.e) ymin , st_xmax(env.e) xmax, st_ymax(env.e) ymax FROM (' + envelope + ') env;'
	cursor = db.cursor()
	cursor.execute(corners_query)
	results = cursor.fetchall()
	xmin = int(results[0][0])
	ymin = int(results[0][1])
	xmax = int(results[0][2])
	ymax = int(results[0][3])
	print(xmin)
	print(ymin)
	print(xmax)
	print(ymax)

	n_horizontal = int(math.ceil((xmax - xmin) / grid_width))
	n_vertical = int(math.ceil((ymax - ymin) / grid_height))
	print('-----------')
	print(n_horizontal)
	print(n_vertical)
	grid = []
	#print(grid)

	finalJSON = '{"type":"FeatureCollection","features":['
	k = 0
	for i in range(n_vertical):
		for j in range(n_horizontal):
			aux_poligno = 'st_GeomFromText(\'POLYGON((' + str(xmin + grid_width * (j)) +  '  ' + str(ymin + grid_height * (i)) + ', ' + str(xmin + grid_width * (j+1)) + ' ' + str(ymin + grid_height * (i)) +  ',' + str(xmin + grid_width * (j+1)) + ' ' + str(ymin + grid_height * (i+1)) + ', ' + str(xmin + grid_width * (j)) + ' ' + str(ymin + grid_height * (i+1)) + ',' + str(xmin + grid_width * (j)) +  '  ' + str(ymin + grid_height * (i)) +  '))\',3763)'  
			query_poligno = 'SELECT ' + aux_poligno + ' poly'
			#cursor = db.cursor()
			#cursor.execute(query_poligno)
			#results = cursor.fetchall()
			#print(results)
			#aux_query2 = 'st_x(st_transform(' + points + ',3763)) >= ' +  str(xmin + grid_width * (j))   + ' AND st_x(st_transform(' + points + ',3763)) <= ' +  str(xmin + grid_width * (j+1))   +' AND st_y(st_transform(' + points + ',3763)) >= ' + str(ymin + grid_height * (i)) + ' AND st_y(st_transform(' + points + ',3763)) <= ' + str(ymin + grid_height * (i+1))  
			#grid_query = 'SELECT count(*) FROM projBD WHERE ' + aux_query2 + ';'
			grid_query2 = 'SELECT count(*)  FROM  projBD ,(' + query_poligno + ') p WHERE st_contains(p.poly,st_transform(' + points + ',3763));'
			polygon_query = 'SELECT st_asGeoJSON(st_transform(p.poly,4326)) FROM (' + query_poligno + ') p;'
			cursor = db.cursor()
			cursor.execute(grid_query2)
			results = cursor.fetchall()
			total = int(results[0][0])
			cursor = db.cursor()
			cursor.execute(polygon_query)
			results = cursor.fetchall()
			if k > 0:
				finalJSON += ','
			finalJSON += '{"type":"Feature","properties":{"id":"Region' + str(k) + '", "style":{"fill":"True"}},"geometry":' + results[0][0] + '}'
			k += 1
			grid.append(total)
	#grid.reverse()
	finalJSON += ']}'
	finalJSON = json.loads(finalJSON)
	print(finalJSON)
	#print(grid)
	col1 = ['Region' + str(i) for i in range(k)]
	d = {'ID' : col1 , 'Services' : grid}
	data2 = pd.DataFrame(data=d)
	data2['ID'] = data2['ID'].astype(str)
	data2['Services'] = data2['Services'].astype(int)

	print(data2)
	folium.Choropleth(
	    geo_data =finalJSON,
	    data=data2,
	    bins = 8,
	    columns=['ID', 'Services'],
	    key_on= 'feature.properties.id',
	    fill_color=  'YlOrRd',
	    legend_name='Taxi Services - ' + points,
	    overlay = True,
	    name = points,
	    show = False,
	    highlight = True
	).add_to(m)






if __name__ == '__main__':

	#print(sys.argv)
	if len(sys.argv) < 4 or len(sys.argv) > 5:
		print("Usage: python PROJBD.py (divisoes/grelha) (inicio/fim) (divisao OU largura da grelha) (altura da grelha)")
		exit()

	db = psycopg2.connect(user = 'postgres', password = 'postgres' , host = 'localhost', database = 'taxis')
	m = folium.Map([ 41.324253,-8.481969], zoom_start=1)
	color1 = 'YlOrRd'

	assert sys.argv[1] == 'divisoes' or sys.argv[1] == 'grelha', "Argumento 1 deve ser divisoes ou grelha"
	assert sys.argv[2] == 'inicio' or sys.argv[2] == 'fim', "Argumento 2 deve ser inicio ou fim"
	points = ''

	if sys.argv[2] == 'inicio':
		points = 'initial_point'
	else:
		points = 'final_point'
	if sys.argv[1] == 'divisoes':
		assert sys.argv[3] == 'freguesia' or sys.argv[3] == 'concelho' or sys.argv[3] == 'distrito', "Argumento 3 deve ser freguesia, concelho ou distrito"
		height_by_divisions(db,sys.argv[3],points,m,color1)
	else:
		assert sys.argv[3].isdigit(), "Argumento 3 deve ser a largura de cada grelha"
		assert sys.argv[4].isdigit(), "Argumento 4 deve ser a altura de cada grelha"
		heat_grid(db,int(sys.argv[3]),int(sys.argv[4]),points,m ) 
	

	m.save('FINALMAP.html')


#centroid = ' st_x(st_centroid(st_collect(geom))) xcent, st_y(st_centroid(st_collect(geom))) ycent'
#geometry = 'ST_AsGeoJSON(st_boundary(st_union(geom))) g'
#aux_query = 'SELECT ' + grao + ' d, ' + geometry + ', st_xmin(st_envelope(st_collect(st_transform(geom,3763)))) xmin ,st_ymin(st_envelope(st_collect(st_transform(geom,3763)))) ymin,st_xmax(st_envelope(st_collect(st_transform(geom,3763)))) xmax,st_ymax(st_envelope(st_collect(st_transform(geom,3763)))) ymax FROM cont_aad_caop2017 GROUP BY ' + grao
#aux_query2 = 'st_x(st_transform(initial_point,3763)) >= coords.xmin AND st_x(st_transform(initial_point,3763)) <= coords.xmax AND st_y(st_transform(initial_point,3763)) >= coords.ymin AND st_y(st_transform(initial_point,3763)) <=  coords.ymax'
#aux_query3 = 'st_x(st_transform(final_point,3763)) >= coords.xmin AND st_x(st_transform(final_point,3763)) <= coords.xmax AND st_y(st_transform(final_point,3763)) >= coords.ymin AND st_y(st_transform(final_point,3763)) <=  coords.ymax'
#query = 'SELECT  count(*) , coords.g  FROM projBD ,  (' + aux_query + ') coords  WHERE ' + aux_query2 + ' OR  ' + aux_query3 + ' GROUP BY coords.d, coords.g;'

#query2 = 'SELECT geom g FROM cont_aad_caop2017 GROUP BY distrito'
#query3 = 'SELECT st_asgeojson(st_boundary(st_union(g))) FROM (' + query2 + ') a;'
#query4 = 'SELECT ' + grao + ' d , st_boundary(st_union(geom)) front FROM cont_aad_caop2017 GROUP BY ' + grao

#query5 = 'SELECT count(*) , fronteiras.d FROM projBD , (' + query4 + ') fronteiras WHERE st_contains(st_transform(fronteiras.front,3763),st_transform(initial_point,3763)) GROUP BY fronteiras.d;'

