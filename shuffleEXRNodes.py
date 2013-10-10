#first arg must be location of arg

nuke.menu('Nodes').addCommand('CustomScripts/Shuffle EXR Channels', shuffleChannelLayers)

# all available renderers must be listed here
renderers = 'Cineman Vray'
#creates script panel/options
p = nuke.Panel('Smart Comper')
p.addEnumerationPulldown('renderers', renderers)
p.addBooleanCheckBox('AutoCrop', False)
p.addBooleanCheckBox('Add Grade Nodes', False)
#brings up the script panel
ret = p.show()

global dif, light, shadow




######## CINEMAN PASSES ##########
cmDif = ['diffuse']
cmLight = ['specular', 'reflection', 'light']
cmShadow = ['shadow', 'ambient_occlusion']

######## VRAY PASSES ##############
vrDif = ['dif']
vrLight = ['refl', 'lighting', 'spec']
vrShadow = ['gi']

############ MENTALRAY PASSES #############

########## SET PASS NAMES ###########
if p.value('renderers') == 'Cineman':
	dif = cmDif
	light = cmLight
	shadow = cmShadow
elif p.value('renderers') == 'Vray':
	dif = vrDif
	light = vrLight
	shadow = vrShadow
elif p.value('renderers') == 'mentalRay':
	dif = mrDif
	light = mrLight
	shadow = mrShadow
	
	
	

passDict = {'dif' : dif, 'light' : light, 'shadow' : shadow}


def uniqueChannelLayerList(nodeToProcess):
    rawChannelList = nodeToProcess.channels()
    channelLayerList = []
    for channel in rawChannelList:
        channelLayer = channel.split('.')
        channelLayerList.append(channelLayer[0])
    return list(set(channelLayerList))

# getting the selection and filtering to a list of read nodes

def shuffleChannelLayers():
    selectedNodes = nuke.selectedNodes()
    for readNode in selectedNodes:
        #test if it's a read node
        if readNode.Class() == 'Read':
            #grabs our list of channel layers from the unique channel layer list function
            uniqueChannelLayers = sortChannelList(uniqueChannelLayerList(readNode))
			
			layerTypeCounter = 0 
            for layerType in uniqueChannelLayers:
				if layerTypeCounter == 0:
					mode = 'over'
				elif layerTypeCounter == 1:
					mode = 'plus'
				elif layerTypeCounter == 2:
					mode = 'multiply'
				elif layerTypeCounter == 3:
					mode = 'over'
				
				for channelLayer in layerType:
					print 'layerTypeCounter = ', layerTypeCounter, 'channelLayer = ', channelLayer
					
					#create a shuffle node for channelLayer
					shuffleNode = nuke.nodes.Shuffle(name = 'Shuffle_' + channelLayer, postage_stamp = True)
					#set the channel
					shuffleNode.knob('in').setValue(channelLayer)
					# set first input to the read node
					shuffleNode.setInput(0, readNode)
					
					#create a variable that creates a curvetool, that will connect to shuffleNode and perform autocrop if use selected autocrop
					if p.value('AutoCrop') == True:
						createAutoCrop(shuffleNode, channelLayer, readNode)
						if p.value('Add Grade Nodes') == False:
							aInputNode = cropNode
							
					if p.value('Add Grade Nodes') == True:
						gradeNode = nuke.nodes.Grade(name = 'Grade_' + channelLayer)
						if p.value('AutoCrop') == True:
							gradeNode.setInput(0, cropNode)
						else:
							gradeNode.setInput(0, shuffleNode)
						aInputNode = gradeNode
					
					if p.value('Add Grade Nodes') == False and p.value('AutoCrop') == False:
						aInputNode = shuffleNode
					
					#give unique name to first finished shuffled channel
					if layerTypeCounter == 3:
						break
					
					elif layerType.index(channelLayer) == 0 and layerTypeCounter == 0:
						global firstNode
						firstNode = aInputNode
					
					elif layerType.index(channelLayer) == 0 and layerTypeCounter == 1:
						createMergeNode(aInputNode, firstNode, mode, channelLayer)
					#create first merge node with B input connected to current node, and A into the first node
					
					elif layerType.index(channelLayer) >= 1 and layerTypeCounter > 0:
						createMergeNode(aInputNode, mergeNode, mode, channelLayer)
					
					elif layerType.index(channelLayer) >= 0 and layerTypeCounter > 1:
						createMergeNode(aInputNode, mergeNode, mode, channelLayer)
				
					
				layerTypeCounter += 1
							
								
            
def sortChannelList(listUser):
	### The list template will be based on renderer. In the final script, this will more likely be a separate dictionary
	### for each renderer, separating passes into diffusion, specular, and shadow passes -> so we can make sure they merge in the proper modes
	### 
		
	listDif = []
	listLight = []
	listShadow = []
	listExtra = []
		
	print "listUser: ", listUser
	for userChan in listUser:
		matchFound = False
		for channelName in dif:
			buf = "Searching for %s in %s\n" % (channelName, userChan)
			print buf
			if channelName in userChan.lower():
				matchFound = True
				listDif.append(userChan)
				
		
		for channelName in light:
			buf = "Searching for %s in %s\n" % (channelName, userChan)
			print buf
			if channelName in userChan.lower():
				listLight.append(userChan)
				matchFound = True
				
		for channelName in shadow:
			buf = "Searching for %s in %s\n" % (channelName, userChan)
			print buf
			if channelName in userChan.lower():
				listShadow.append(userChan)
				matchFound = True
		
		if matchFound != True:
			listExtra.append(userChan)
		
		
	#eliminates duplicates left over in listUser		
	
	listFinal = [listDif, listLight, listShadow, listExtra]
	print listFinal
	return listFinal

#Creates a dot and mergenode based on the two inputs and the mode. 	
def createMergeNode(input1, input2, mode, channelLayer):
	global mergeNode
	print mode + 'ing %s to %s\n' % (input1.knob('name').value(), input2.knob('name').value())
	dot = nuke.nodes.Dot(inputs = [input1])
	dot.setXYpos(input1.xpos() + input1.screenWidth()/2, input2.ypos() + 100)
	newMergeNode = nuke.nodes.Merge(name = 'Merge_' + channelLayer, operation = mode)
	newMergeNode.setInput(0, input2)
	newMergeNode.setInput(1, dot)
	newMergeNode.setXYpos(input2.xpos(), dot.ypos())
	mergeNode = newMergeNode
	return
	
def createAutoCrop(input1, channelLayer, readNode):
	curveNode = nuke.nodes.CurveTool(name = 'AutoCrop_' + channelLayer, inputs = [input1], operation = 'Auto Crop')				
	nuke.execute(curveNode, readNode.knob('first').value(), readNode.knob('last').value())
	global cropNode
	cropNode = nuke.nodes.Crop(name = 'Crop_' + channelLayer, inputs = [curveNode])
	cropNode.knob('box').copyAnimations(curveNode.knob('autocropdata').animations())
	return
	
shuffleChannelLayers()

