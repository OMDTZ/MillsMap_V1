import matplotlib.pyplot as plt
import os

def count_items(dictionary, value, key1, key2 = None, multiple_choice = False):
	count = 0
	if key2 != None:
		for item in dictionary:
		    if item[key1][key2] == value:
		        count += 1
	else:
		if multiple_choice == False: 
			for item in dictionary:
			    if item[key1] == value:
			        count += 1
		else:
			for item in dictionary:
				if value in item[key1].split():
					count += 1
	return count

def unique_key_counts(dictionary, key1, key2 = None, multiple_choice = False):
	values = []
	value_counts = []

	if multiple_choice == False:
		if key2 != None:
			for item in dictionary:
			    values.append(item[key1][key2])
		else: 
			for item in dictionary:
			    values.append(item[key1])
		unique_values = list(set(values))
		for unique_value in unique_values:
			value_counts.append(count_items(dictionary, unique_value, key1, key2))
	else:
		if key2 == None: 
			for item in dictionary:
			    for element in item[key1].split(' '):
			    	if element not in values:
			    		values.append(element)
		unique_values = values
		for unique_value in unique_values:
			value_counts.append(count_items(dictionary, unique_value, key1, key2, multiple_choice))

	
	return unique_values, value_counts


def charts(submissions_machine, submissions):
	operational_count = count_items(submissions_machine, key1 = 'operational_mill', value = 'yes')
	not_operational_count = count_items(submissions_machine, key1 = 'operational_mill', value = 'no')
	labels = 'Operational', 'Not operational'
	colors = ['#6495ED', '#EEDC82']
	sizes = [operational_count, not_operational_count]
	explode = (0, 0.03)  # only "explode" the 2nd slice (i.e. 'Hogs')

	fig, ax1 = plt.subplots()
	ax1.pie(sizes, labels=labels, explode = explode, colors=colors, autopct='%1.1f%%',
	        shadow=False, startangle=90)
	ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
	if not os.path.exists('app/static/figures'):
		outdir = os.makedirs('app/static/figures')
	fig.savefig('app/static/figures/piechart.jpg', bbox_inches='tight')   # save the figure to file
	plt.close(fig)   

	#Mill types
	mill_types, mill_type_counts = unique_key_counts(submissions_machine, key1 = 'mill_type')
	fig1, ax1 = plt.subplots()
	plt.barh(mill_types, mill_type_counts, align='center')
	for s in ['top', 'bottom', 'left', 'right']:
	    ax1.spines[s].set_visible(False)
	ax1.xaxis.set_ticks_position('none')
	ax1.yaxis.set_ticks_position('none')
	ax1.grid(b = True, color ='grey',
        linestyle ='-.', linewidth = 0.5,
        alpha = 0.2)
	ax1.invert_yaxis()
	# Add annotation to bars
	for i in ax1.patches:
	    plt.text(i.get_width()+0.2, i.get_y()+0.5,
	             str(round((i.get_width()), 2)),
	             fontsize = 10, fontweight ='bold',
	             color ='grey')
	fig1.savefig('app/static/figures/barplot.jpg', bbox_inches='tight')   # save the figure to file
	plt.close(fig)   

	#types of grains
	grain_types, grain_type_counts = unique_key_counts(submissions_machine, key1 = 'commodity_milled', multiple_choice=True)
	fig2, ax2 = plt.subplots()
	plt.barh(grain_types, grain_type_counts, align='center')
	for s in ['top', 'bottom', 'left', 'right']:
	    ax2.spines[s].set_visible(False)
	ax2.xaxis.set_ticks_position('none')
	ax2.yaxis.set_ticks_position('none')
	ax2.grid(b = True, color ='grey',
        linestyle ='-.', linewidth = 0.5,
        alpha = 0.2)
	ax2.invert_yaxis()
	# Add annotation to bars
	for i in ax2.patches:
	    plt.text(i.get_width()+0.2, i.get_y()+0.5,
	             str(round((i.get_width()), 2)),
	             fontsize = 10, fontweight ='bold',
	             color ='grey')
	fig2.savefig('app/static/figures/barplot_commodity_milled.jpg', bbox_inches='tight')   # save the figure to file
	plt.close(fig)  

	#Flour fortification
	fortify_types, fortify_type_counts = unique_key_counts(submissions, key1 = 'Packaging', key2 = 'flour_fortified')
	fig2, ax2 = plt.subplots()
	plt.barh(fortify_types, fortify_type_counts, align='center')
	for s in ['top', 'bottom', 'left', 'right']:
	    ax2.spines[s].set_visible(False)
	ax2.xaxis.set_ticks_position('none')
	ax2.yaxis.set_ticks_position('none')
	ax2.grid(b = True, color ='grey',
        linestyle ='-.', linewidth = 0.5,
        alpha = 0.2)
	ax2.invert_yaxis()
	# Add annotation to bars
	for i in ax2.patches:
	    plt.text(i.get_width()+0.2, i.get_y()+0.5,
	             str(round((i.get_width()), 2)),
	             fontsize = 10, fontweight ='bold',
	             color ='grey')
	fig2.savefig('app/static/figures/barplot_flour_fortified.jpg', bbox_inches='tight')   # save the figure to file
	plt.close(fig)  
