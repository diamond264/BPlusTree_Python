# basic configurations are here
data_file = 'data.csv'
key_attributes = ['sales', 'price']
tid = 'tid'

leaf = 0
internal = 1

user_interface = '''==== B+ tree program ====
1. LOAD
2. PRINT
3. INSERT
4. DELETE
5. SEARCH
6. RANGE_SEARCH
7. EXIT
=========================
SELECT MENU: '''

# compares two key values,
# then returns 1 if a is bigger than b,
# -1 if b is bigger than a
# 0 otherwise
def compare_tuple(a, b):
	a_first, a_second = a
	b_first, b_second = b

	if a_first > b_first:
		return 1
	elif a_first < b_first:
		return -1

	if a_second > b_second:
		return 1
	elif a_second < b_second:
		return -1

	return 0


# the class for node in b+ tree
class Node:
	def __init__(self, status, data = []):
		self.status = status
		self.data = data
		self.children = []
		self.parent = None
		self.next = None
		self.prev = None

	# reset is used when reinitializing the root
	def reset(self):
		self.status = leaf
		self.data = []
		self.children = []
		self.parent = None
		self.next = None
		self.prev = None

	# insert data in leaf node
	def insert_leaf(self, new_elem):
		for i, elem in enumerate(self.data):
			comparison = compare_tuple(elem['key'], new_elem['key'])
			if comparison == 0:
				elem.append(new_elem['value'])
				return

			elif comparison > 0:
				self.data.insert(i, new_elem)
				return

		self.data.append(new_elem)

	# insert data in internal node
	def insert_internal(self, new_elem):
		for i, elem in enumerate(self.data):
			comparison = compare_tuple(elem, new_elem)

			if comparison > 0:
				self.data.insert(i, new_elem)
				return

		self.data.append(new_elem)

	# add child in node
	# makes the child's parent to self
	def add_child(self, node):
		new_elem = node.data[0]
		if node.status is leaf:
			new_elem = new_elem['key']

		node.parent = self
		for i, child in enumerate(self.children):
			elem = child.data[0]
			if child.status is leaf:
				elem = elem['key']
			comparison = compare_tuple(elem, new_elem)
			if comparison > 0:
				self.children.insert(i, node)
				return

		self.children.append(node)


# class for b+ tree
class B_plus_tree:
	def __init__(self, order=3):
		# default order is 3, initial node is empty leaf
		self.order = order
		self.root = Node(leaf)

	def load(self, filename, start_tid, end_tid):
		# reset the root node
		self.root.reset()

		column_dic = {}
		with open(filename, 'r', encoding='utf-8') as reader:
			lines = list(reader)
			# the first line means column header, make it to dictionary
			cols = lines[0].strip().split(',')
			for i, col in enumerate(cols):
				column_dic[col] = i

			if start_tid <= 0 or end_tid > len(lines)-1 or start_tid > end_tid:
				print('inex out of range... failed loading.')
				return -1

			# import only key values, parse it, then insert it into b+ tree
			for i in range(start_tid, end_tid+1):
				cols = lines[i].strip().split(',')
				key_tuple = [int(cols[column_dic[att]]) for att in key_attributes]
				key_tuple = tuple(key_tuple)
				value = [int(cols[column_dic[tid]])]
				curr_data = {'key':key_tuple, 'value':value}
				self.insert_leaf(curr_data)

		print('B+ Tree is built.')
		print('')

	def insert(self, filename, tuple_id):
		# find tuple_id in data file, then insert it to b+ tree
		column_dic = {}
		with open(filename, 'r', encoding='utf-8') as reader:
			lines = list(reader)
			cols = lines[0].strip().split(',')
			for i, col in enumerate(cols):
				column_dic[col] = i

			if tuple_id <= 0 or tuple_id > len(lines)-1:
				print('inex out of range... failed loading.')
				print('')
				return -1

			cols = lines[tuple_id].strip().split(',')
			key_tuple = [int(cols[column_dic[att]]) for att in key_attributes]
			key_tuple = tuple(key_tuple)
			value = [int(cols[column_dic[tid]])]
			curr_data = {'key':key_tuple, 'value':value}
			# insert it as a leaf
			self.insert_leaf(curr_data)

		print('Tuple #{tuple_id} is inserted.'.format(tuple_id=tuple_id))
		print('')

	def print(self):
		# print the current state of b+ tree
		# I used bfs with queue for printing
		root = self.root
		nodes = [root]
		level = []

		# bfs queue algorithm
		# when popping, push its children
		while len(nodes) != 0:
			next_nodes = []
			level.append(nodes.copy())

			while nodes:
				node = nodes.pop(0)
				next_nodes = next_nodes + node.children

			nodes = next_nodes

		# print all data in level list
		i = -1
		for internal_nodes in level[:-1]:
			i = i+1
			print('Level {level}: '.format(level=i+1), end='')
			for node in internal_nodes:
				print(node.data, end=' ')
			print('\n')

		i = i+1
		leaf_nodes = level[-1]
		print('Level {level}: '.format(level=i+1), end='')

		for i, node in enumerate(leaf_nodes):
			print('[', end='')
			for j, data in enumerate(node.data):
				print('('+str(data['key'])+', '+str(data['value'])+')', end='')
				if j != len(node.data)-1:
					print(', ', end='')
			print(']', end='')
			if i != len(leaf_nodes)-1:
				print(' --> ', end='')
			else:
				print('\n')

	def insert_leaf(self, new_elem):
		# function for inserting new_elem as leaf in b+ tree
		root = self.root
		exist_elem, node = self.search(root, new_elem['key'])

		# if the value already exists, append it to value list
		if exist_elem is not None:
			exist_elem['value'] = exist_elem['value']+new_elem['value']
			return 1

		# if we have space to insert leaf at node, insert it
		if len(node.data) < self.order - 1:
			node.insert_leaf(new_elem)
			return 1

		# if not, we should solve the overflow
		# split the node, then choose one value as indicator
		# then raise the indicator to index node
		median_idx = self.order // 2
		node.insert_leaf(new_elem)
		new_leaf_left = Node(leaf, node.data[:median_idx])
		new_leaf_right = Node(leaf, node.data[median_idx:])
		new_leaf_left.next = new_leaf_right
		new_leaf_right.prev = new_leaf_left

		if node.prev is not None:
			node.prev.next = new_leaf_left
			new_leaf_left.prev = node.prev
		if node.next is not None:
			new_leaf_right.next = node.next
			node.next.prev = new_leaf_right

		median_key = node.data[median_idx]

		prev_parent = node.parent
		if prev_parent is None:
			# it means, the node was root
			# then make new index node as root
			new_node = Node(internal, [median_key['key']])
			new_node.add_child(new_leaf_right)
			new_node.add_child(new_leaf_left)
			self.root = new_node
			return 1

		prev_parent.children.remove(node)
		node_1, node_2 = self.insert_internal(prev_parent, median_key['key'])
		# after insert the indicator to index node(internal node),
		# connect the new leaf nodes as child of the result node in insert_internal function
		node_1.add_child(new_leaf_left)
		node_2.add_child(new_leaf_right)

		return 1

	def insert_internal(self, node, new_elem):
		# function for inserting new_elem as index node in b+ tree
		if len(node.data) < self.order - 1:
			# if we have space in node, insert it
			node.insert_internal(new_elem)
			return node, node

		# if overflow occurs, split the node
		# then choose one median indicator between datas in node
		median_idx = self.order // 2
		node.insert_internal(new_elem)
		new_node_left = Node(internal, node.data[:median_idx])
		new_node_right = Node(internal, node.data[median_idx+1:])

		prev_data = node.data
		median_key = prev_data[median_idx]
		prev_children = node.children
		# conncecting the previous children to new node
		for child in prev_children:
			elem = child.data[0]
			if child.status is leaf:
				elem = elem['key']
			comparison = compare_tuple(median_key, elem)
			if comparison > 0:
				new_node_left.add_child(child)
			else:
				new_node_right.add_child(child)

		prev_parent = node.parent
		if prev_parent is None:
			# it means that the node is root node
			# make the new node including indicator, then make it as root
			# give the return value which the function caller should add child
			new_node = Node(internal, [median_key])
			new_node.add_child(new_node_left)
			new_node.add_child(new_node_right)
			self.root = new_node
			comparison = compare_tuple(median_key, new_elem)
			if comparison > 0:
				return new_node.children[0], new_node.children[0]
			elif comparison < 0:
				return new_node.children[1], new_node.children[1]
			else:
				return new_node.children[0], new_node.children[1]

		prev_parent.children.remove(node)
		node_1, node_2 = self.insert_internal(prev_parent, median_key)
		# after insert the indicator to index node(internal node),
		# connect the new nodes as child of the result node in recursive function

		node_1.add_child(new_node_left)
		node_2.add_child(new_node_right)

		# give the return value which the function caller should add child
		comparison = compare_tuple(median_key, new_elem)
		if comparison > 0:
			return new_node_left, new_node_left
		elif comparison < 0:
			return new_node_right, new_node_right
		else:
			return new_node_left, new_node_right

	def delete(self, filename, tuple_id):
		# get the key value from data file with tuple id
		# then remove the node with key value in b+ tree
		column_dic = {}
		with open(filename, 'r', encoding='utf-8') as reader:
			lines = list(reader)
			cols = lines[0].strip().split(',')
			for i, col in enumerate(cols):
				column_dic[col] = i

			if tuple_id <= 0 or tuple_id > len(lines)-1:
				print('inex out of range... failed loading.')
				print('')
				return -1

			cols = lines[tuple_id].strip().split(',')
			key_tuple = [int(cols[column_dic[att]]) for att in key_attributes]
			key_tuple = tuple(key_tuple)
			value = [int(cols[column_dic[tid]])]
			new_elem = {'key':key_tuple, 'value':value}

		leaf_elem, node = self.search(self.root, new_elem['key'])

		# the case such leaf element doesn't exist
		if leaf_elem is None:
			print('No such tuple in storage.')
			print('')
			return -1

		# else, if there exists two values in b+ tree
		# remove one value in value list
		if len(leaf_elem['value']) > 1:
			leaf_elem['value'].remove(tuple_id)
			return 1

		# else, if the leaf has more than one data or node is root
		# just remove one data from node
		if len(node.data) > self.order//2 or node is self.root:
			node.data.remove(leaf_elem)
			return 1

		# else, if the parent has more than one data
		# it has more than two children
		# just remove the node, and remove it from parent
		parent = node.parent
		if len(parent.data) > self.order // 2:
			for i, child in enumerate(parent.children):
				if child is node:
					index = i

			if index == 0 or index == 1:
				parent.data.remove(parent.data[0])
			else:
				parent.data.remove(parent.data[1])

			if node.next is not None:
				node.next.prev = node.prev
			if node.prev is not None:
				node.prev.next = node.next

			parent.children.remove(node)
			return 1

		# else, if the sibling which has same parent has more than one data
		# borrow one data from the sibling node
		if node.next is not None and node.next.parent is parent:
			if len(node.next.data) >= 2:
				parent.data = [node.next.data[1]['key']]
				node.data = [node.next.data[0]]
				node.next.data = [node.next.data[1]]
				return 1

		if node.prev is not None and node.prev.parent is parent:
			if len(node.prev.data) >= 2:
				parent.data = [node.prev.data[1]['key']]
				node.data = [node.prev.data[1]]
				node.prev.data = [node.prev.data[0]]
				return 1

		# else, if the parent is root
		# remove node and the other child will be the root
		if parent is self.root:
			if node.next is not None:
				node.next.prev = node.prev
			if node.prev is not None:
				node.prev.next = node.next

			parent.children.remove(node)
			self.root = parent.children[0]
			self.root.parent = None
			return 1

		# else, it means underflow
		# borrow child from sibling, or get merged into sibling
		if node.next is not None:
			node.next.prev = node.prev
		if node.prev is not None:
			node.prev.next = node.next

		parent.children.remove(node)
		self.merge_node(parent)
		return 1

	def merge_node(self, node):
		parent = node.parent

		# if node is first child, second child is sibling
		if parent.children[0] is node:
			sibling = parent.children[1]
			# the case for borrowing
			if len(sibling.children) == 3:
				new_child = sibling.children[0]
				sibling.children.remove(new_child)
				node.add_child(new_child)
				node.data = [parent.data[0]]
				parent.data[0] = sibling.data[0]
				sibling.data.remove(sibling.data[0])
				return 1

			# the case for merging
			new_child = node.children[0]
			parent.children.remove(node)
			sibling.data.insert(0, parent.data[0])
			sibling.add_child(new_child)
			parent.data.remove(parent.data[0])

			if len(parent.children) == 2:
				return 1

			elif parent is self.root:
				self.root = sibling
				self.root.parent = None
				return 1

			else:
				self.merge_node(parent)
				return 1

		# from here, same with above for other cases
		elif parent.children[1] is node:
			if len(parent.children) == 3:
				sibling = parent.children[2]
				if len(sibling.children) == 3:
					new_child = sibling.children[0]
					sibling.children.remove(new_child)
					node.add_child(new_child)
					node.data = [parent.data[1]]
					parent.data[1] = sibling.data[0]
					sibling.data.remove(sibling.data[0])
					return 1

				new_child = node.children[0]
				parent.children.remove(node)
				sibling.data.insert(0, parent.data[1])
				sibling.add_child(new_child)
				parent.data.remove(parent.data[1])

				if len(parent.children) == 2:
					return 1

				elif parent is self.root:
					self.root = sibling
					self.root.parent = None
					return 1

				else:
					self.merge_node(parent)
					return 1

			sibling = parent.children[0]
			if len(sibling.children) == 3:
				new_child = sibling.children[2]
				sibling.children.remove(new_child)
				node.add_child(new_child)
				node.data = [parent.data[0]]
				parent.data[0] = sibling.data[1]
				sibling.data.remove(sibling.data[1])
				return 1

			new_child = node.children[0]
			parent.children.remove(node)
			sibling.data.append(parent.data[0])
			sibling.add_child(new_child)
			parent.data.remove(parent.data[0])

			if len(parent.children) == 2:
				return 1

			elif parent is self.root:
				self.root = sibling
				self.root.parent = None
				return 1

			else:
				self.merge_node(parent)
				return 1

		else:
			sibling = parent.children[1]
			if len(sibling.children) == 3:
				new_child = sibling.children[2]
				sibling.children.remove(new_child)
				node.add_child(new_child)
				node.data = [parent.data[1]]
				parent.data[1] = sibling.data[1]
				sibling.data.remove(sibling.data[1])
				return 1

			new_child = node.children[0]
			parent.children.remove(node)
			sibling.data.append(parent.data[1])
			sibling.add_child(new_child)
			parent.data.remove(parent.data[1])

			if len(parent.children) == 2:
				return 1

	def search_from_root(self, filename, new_elem):
		# search the value with key by self.search function
		# then print all of its attributes in data file
		result, node = self.search(self.root, new_elem)

		if result is None:
			print('No such tuple in storage.')
			print('')
			return

		found_tids = [str(i) for i in result['value']]
		print('Found tuple IDs : [{found_tids}]'.format(\
			found_tids=','.join(found_tids)))

		column_dic = {}
		with open(filename, 'r', encoding='utf-8') as reader:
			lines = list(reader)
			cols = lines[0].strip().split(',')
			for i, col in enumerate(cols):
				column_dic[col] = i

			print('Attributes : <{attributes}>'.format(\
				attributes=','.join(column_dic.keys())))

			for i in result['value']:
				cols = lines[i+1].strip().split(',')
				print('Tuple #{tuple_id} : <{cols}>'.format(\
					tuple_id=i, cols=','.join(cols)))

		print('')

	def search_range(self, filename, start, end):
		# each leaf nodes are connected by pointer 'next', 'prev'
		# I used these pointers to do search range quickly
		result, node = self.search(self.root, start)

		search_result = []
		while compare_tuple(end, node.data[0]['key']) >= 0:
			for elem in node.data:
				lower_condition = compare_tuple(start, elem['key']) <= 0
				upper_condition = compare_tuple(end, elem['key']) >= 0
				if lower_condition and upper_condition:
					search_result.append(elem)

			node = node.next
			if node is None:
				break

		if len(search_result) == 0:
			print('No such tuple in storage.')
			print('')
			return

		found_pairs = str([(i['key'], i['value']) for i in search_result])
		print('Found pairs : [{found_pairs}]'.format(found_pairs=found_pairs))

		result = []
		for i in search_result:
			result = result + i['value']

		column_dic = {}
		with open(filename, 'r', encoding='utf-8') as reader:
			lines = list(reader)
			cols = lines[0].strip().split(',')
			for i, col in enumerate(cols):
				column_dic[col] = i

			print('Attributes : <{attributes}>'.format(\
				attributes=','.join(column_dic.keys())))

			for i in result:
				cols = lines[i+1].strip().split(',')
				print('Tuple #{tuple_id} : <{cols}>'.format(\
					tuple_id=i, cols=','.join(cols)))

		print('')

	def search(self, node, new_elem):
		# by comparing the key values, use tree traversal
		# if we reach at leaf node, return the element if exists
		# if not exists, return None
		if node.status is leaf:
			for elem_dic in node.data:
				elem = elem_dic['key']
				if compare_tuple(elem, new_elem) == 0:
					return elem_dic, node
			return None, node

		for i, elem in enumerate(node.data):
			compared = compare_tuple(elem, new_elem)
			if compared > 0:
				child = node.children[i]
				return self.search(child, new_elem)

		child = node.children[i+1]
		return self.search(child, new_elem)


def main():
	tree = B_plus_tree()

	while True:
		selected = int(input(user_interface))

		if selected == 1:
			print('========= LOAD ==========')
			start_tid = int(input('  LOAD_START_TID: '))
			end_tid = int(input('  LOAD_END_TID: '))
			print('LOADING ....')
			tree.load(data_file, start_tid, end_tid)

		elif selected == 2:
			print('========= PRINT =========')
			tree.print()

		elif selected == 3:
			print('======== INSERT =========')
			tuple_id = int(input('  TUPLE_ID: '))
			tree.insert(data_file, tuple_id)

		elif selected == 4:
			print('======== DELETE =========')
			tuple_id = int(input('  TUPLE_ID: '))
			success = tree.delete(data_file, tuple_id)
			if success == 1:
				print('Tuple #{tuple_id} is deleted.'.format(tuple_id=tuple_id))
				print('')

		elif selected == 5:
			print('======== SEARCH =========')
			search_key = input('  SEARCH KEY: ')
			search_key = search_key.strip()[1:-1].split(',')
			search_key = tuple([int(i) for i in search_key])
			tree.search_from_root(data_file, search_key)

		elif selected == 6:
			print('===== RANGE_SEARCH ======')
			search_range = input('  SEARCH RANGE: ')
			search_range = search_range.strip()[1:-1].split('),')
			search_start = search_range[0].strip()[1:].split(',')
			search_start = tuple([int(i) for i in search_start])
			search_end = search_range[1].strip()[1:-1].split(',')
			search_end = tuple([int(i) for i in search_end])
			tree.search_range(data_file, search_start, search_end)

		elif selected == 7:
			print('========= EXIT ==========')
			break

main()

