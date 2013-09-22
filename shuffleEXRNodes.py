#first arg must be location of arg

nuke.menu('Nodes').addCommand('CustomScripts/Shuffle EXR Channels', shuffleChannelLayers)

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
			
			
            for channelLayer in uniqueChannelLayers:
                #create a shuffle node for channelLayer
                shuffleNode = nuke.nodes.Shuffle(name = 'Shuffle_' + channelLayer)
                #set the channel
                shuffleNode.knob('in').setValue(channelLayer)
                # set first input to the read node
                shuffleNode.setInput(0, readNode)
                #create a variable that creates a curvetool, that will connect to shuffleNode and perform autocrop
                curveNode = nuke.nodes.CurveTool(name = 'AutoCrop_' + channelLayer, 
                                                                    inputs = [shuffleNode],
                                                                    operation = 'Auto Crop')
				
                nuke.execute(curveNode, readNode.knob('first').value(), readNode.knob('last').value())
                cropNode = nuke.nodes.Crop(name = 'Crop_' + channelLayer, inputs = [curveNode])
                cropNode.knob('box').copyAnimations(curveNode.knob('autocropdata').animations())
				
				#give unique name to first finished shuffled channel
				if uniqueChannelLayers.index(channelLayer) == 0:
					firstNode = cropNode
				#create first merge node with B input connected to current node, and A into the first node
				elif uniqueChannelLayers.index(channelLayer) == 1:
					mergeNode = nuke.nodes.Merge(name = 'Merge_' + channelLayer)
					mergeNode.setInput(0, firstNode)
					mergeNode.setInput(1, cropNode)
			
				#create subsequent merge nodes with B input to previous merge, A to current node
				elif uniqueChannelLayers.index(channelLayer) > 1:
					newMergeNode = nuke.nodes.Merge(name = 'Merge_' + channelLayer)
					newMergeNode.setInput(0, mergeNode)
					newMergeNode.setInput(1, cropNode)
					mergeNode = newMergeNode
								
            
def sortChannelList(listUser):
	### The list template will be based on renderer. In the final script, this will more likely be a separate dictionary
	### for each renderer, separating passes into diffusion, specular, and shadow passes -> so we can make sure they merge in the proper modes
	### 
	listTemplate = ['diffuse', 'specular', 'reflection',  'shadow', 'ambient_occlusion']
	listFinal = []
	print "Beginning User List: ", listUser, "List Template: ", listTemplate

	for tempChan in listTemplate:
		channel = tempChan
		for userChan in listUser:
			if channel in userChan.lower():
				listFinal.append(userChan)
				listUser.pop(listUser.index(userChan))
	
	return listFinal
	
shuffleChannelLayers()

