
################### :D #################
# all available renderers must be listed here
renderers = 'Cineman Vray'
#creates script panel/options
p = nuke.Panel('Smart Comper')
p.addEnumerationPulldown('renderers', renderers)
p.addBooleanCheckBox('AutoCrop', False)
p.addBooleanCheckBox('Add Grade Nodes', False)
#brings up the script panel
ret = p.show()

offsetXPos = 100
offsetYPos = 50

global dif, light, shadow

################### :D #################
######## CINEMAN PASSES ##########
cmDif = ['diffuse']
cmLight = [
	'specular', 
	'reflection', 
	'light',
	]
cmShadow = [
	'shadow',
	'ambient_occlusion'
	]
cmMoBlur = ['motion_vector']
cmDepth = ['depth']

################### :D #################
######## VRAY PASSES ##############
vrDif = ['dif']
vrLight = ['refl', 'lighting', 'spec']
vrShadow = ['gi']
vrMoBlur = ['velocity']
vrDepth = ['depth']

################### :D #################
############ MENTALRAY PASSES #############

################### :D #################
########## SET PASS NAMES ###########
if p.value('renderers') == 'Cineman':
	dif = cmDif
	light = cmLight
	shadow = cmShadow
	moBlur = cmMoBlur
	depth = cmDepth
elif p.value('renderers') == 'Vray':
	dif = vrDif
	light = vrLight
	shadow = vrShadow
	moBlur = vrMoBlur
	depth = vrDepth
elif p.value('renderers') == 'mentalRay':
	dif = mrDif
	light = mrLight
	shadow = mrShadow
	moBlur = mrMoBlur
	depth = mrDepth
	

passDict = {'dif' : dif, 'light' : light, 'shadow' : shadow}

################### :D #################
def uniqueChannelLayerList(nodeToProcess):
    rawChannelList = nodeToProcess.channels()
    channelLayerList = []
    for channel in rawChannelList:
        channelLayer = channel.split('.')
        channelLayerList.append(channelLayer[0])
    return list(set(channelLayerList))

################### :D #################
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
					newShuffleNode = nuke.nodes.Shuffle(name = 'Shuffle_' + channelLayer, postage_stamp = True)
					#set the channel
					newShuffleNode.knob('in').setValue(channelLayer)
					# set first input to the read node
					newShuffleNode.setInput(0, readNode)
					newShuffleNode.setYpos(readNode.ypos() + 100)
					if layerTypeCounter > 0 or layerType.index(channelLayer) > 0:
						newShuffleNode.setXpos(shuffleNode.xpos() + 100)
					shuffleNode = newShuffleNode
					
					#create a variable that creates a curvetool, that will connect to shuffleNode and perform autocrop if user selected autocrop
					if p.value('AutoCrop') == True:
						createAutoCrop(shuffleNode, channelLayer, readNode)
						if p.value('Add Grade Nodes') == False:
							aInputNode = cropNode
					
					# Creates grade nodes on all passes if user selected them
					if p.value('Add Grade Nodes') == True:
						gradeNode = nuke.nodes.Grade(name = 'Grade_' + channelLayer)
						#sets input to autocrop nodes if user used autocrop
						if p.value('AutoCrop') == True:
							gradeNode.setInput(0, cropNode)
							gradeNode.setYpos(cropNode.ypos() + 20)
						#sets input to shuffleNode if user did not use Autocrop
						else:
							gradeNode.setInput(0, shuffleNode)
							gradeNode.setYpos(shuffleNode.ypos() + 85)
						#sets the aInputNode variable (used as an input for mergeNodes) to the gradeNode
						aInputNode = gradeNode
					
					if p.value('Add Grade Nodes') == False and p.value('AutoCrop') == False:
						aInputNode = shuffleNode
					
					#give unique name to first finished shuffled channel
					if layerTypeCounter == 3:
						createZBlur(aInputNode, mergeNode, channelLayer)
					
					elif layerTypeCounter == 4:
						createMoBlur(aInputNode, mergeNode, channelLayer)
						
					elif layerTypeCounter == 5:
						pass
					
					elif layerType.index(channelLayer) == 0 and layerTypeCounter == 0:
						global firstNode
						aInputNode.setXpos(readNode.xpos())
						firstNode = aInputNode
					
					elif layerType.index(channelLayer) == 0 and layerTypeCounter == 1:
						createMergeNode(aInputNode, firstNode, mode, channelLayer)
					#create first merge node with B input connected to current node, and A into the first node
					
					elif layerType.index(channelLayer) >= 1 and layerTypeCounter > 0:
						createMergeNode(aInputNode, mergeNode, mode, channelLayer)
					
					elif layerType.index(channelLayer) >= 0 and layerTypeCounter > 1:
						createMergeNode(aInputNode, mergeNode, mode, channelLayer)
				
					
				layerTypeCounter += 1
							
								
################### :D #################
def sortChannelList(listUser):
	################### :D #################
	### The list template will be based on renderer. In the final script, this will more likely be a separate dictionary
	### for each renderer, separating passes into diffusion, specular, and shadow passes -> so we can make sure they merge in the proper modes
	### 
		
	listDif = []
	listLight = []
	listShadow = []
	listDepth = []
	listMoBlur = []
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
				
		for channelName in depth:
			if channelName in userChan.lower():
				listDepth.append(userChan)
				matchFound = True
			
		for channelName in moBlur:
			if channelName in userChan.lower():
				listMoBlur.append(userChan)
				matchFound = True
		
		if matchFound != True:
			listExtra.append(userChan)
		
	################### :D #################	
	#eliminates duplicates left over in listUser		
	
	listFinal = [listDif, listLight, listShadow, listDepth, listMoBlur, listExtra]
	print listFinal
	return listFinal

################### :D #################
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

################### :D #################	
def createAutoCrop(input1, channelLayer, readNode):
	curveNode = nuke.nodes.CurveTool(name = 'AutoCrop_' + channelLayer, inputs = [input1], operation = 'Auto Crop', ypos = input1.ypos() + 20)				
	nuke.execute(curveNode, readNode.knob('first').value(), readNode.knob('last').value())
	global cropNode
	cropNode = nuke.nodes.Crop(name = 'Crop_' + channelLayer, inputs = [curveNode], ypos = curveNode.ypos() + 20)
	cropNode.knob('box').copyAnimations(curveNode.knob('autocropdata').animations())
	return

################### :D #################
def createZBlur(input1, input2, channelLayer):
	global mergeNode
	dot = nuke.nodes.Dot(inputs = [input1])
	dot.setXYpos(input1.xpos() + input1.screenWidth()/2, input2.ypos() + 100)
	shuffleCopyNode = nuke.nodes.ShuffleCopy(name = "ShuffleCopy" + channelLayer, inputs = [input2, dot])
	shuffleCopyNode.knob('in').setValue('rgb')
	shuffleCopyNode.knob('out').setValue('depth')
	shuffleCopyNode.setXYpos(input2.xpos(), dot.ypos())
	shuffleCopyNode.knob('red').setValue(True)
	depthNode = nuke.nodes.ZBlur(name = 'ZBlur' + channelLayer, inputs = [shuffleCopyNode])
	depthNode.knob('max_size').setValue(0)
	mergeNode = depthNode
	return

################### :D #################	
def createMoBlur(input1, input2, channelLayer):
	global mergeNode
	dot = nuke.nodes.Dot(inputs = [input1])
	dot.setXYpos(input1.xpos() + input1.screenWidth()/2, input2.ypos() + 100)
	shuffleCopyNode = nuke.nodes.ShuffleCopy(name = "ShuffleCopy" + channelLayer, inputs = [input2, dot])
	shuffleCopyNode.knob('in').setValue('rgb')
	shuffleCopyNode.knob('out').setValue('motion')
	shuffleCopyNode.setXYpos(input2.xpos(), dot.ypos())
	shuffleCopyNode.knob('red').setValue(True)
	shuffleCopyNode.knob('green').setValue(True)
	shuffleCopyNode.knob('blue').setValue(True)
	shuffleCopyNode.knob('alpha').setValue(True)
	depthNode = nuke.nodes.VectorBlur(name = 'VectorBlur' + channelLayer, inputs = [shuffleCopyNode])
	depthNode.knob('max_size').setValue(0)
	mergeNode = depthNode
	return
	
################### :D #################		
shuffleChannelLayers()

