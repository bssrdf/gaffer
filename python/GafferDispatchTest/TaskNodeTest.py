##########################################################################
#
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import os
import unittest
import itertools

import IECore

import Gaffer
import GafferTest
import GafferDispatch
import GafferDispatchTest

class TaskNodeTest( GafferTest.TestCase ) :

	def testTypeNamePrefixes( self ) :

		self.assertTypeNamesArePrefixed( GafferDispatch )

	def testDefaultNames( self ) :

		self.assertDefaultNamesAreCorrect( GafferDispatch )

	def testNodesConstructWithDefaultValues( self ) :

		self.assertNodesConstructWithDefaultValues( GafferDispatch )

	def testDerivedClasses( self ) :

		self.assertTrue( issubclass( GafferDispatchTest.LoggingTaskNode, GafferDispatch.TaskNode ) )
		self.assertTrue( isinstance( GafferDispatchTest.LoggingTaskNode(), GafferDispatch.TaskNode ) )

	def testHash( self ) :

		c1 = Gaffer.Context()
		c1.setFrame( 1 )
		c2 = Gaffer.Context()
		c2.setFrame( 2 )
		c3 = Gaffer.Context()
		c3.setFrame( 3.0 )

		# Hashes that don't use the context are equivalent
		n = GafferDispatchTest.LoggingTaskNode()
		with c1 :
			c1h = n["task"].hash()
		with c2 :
			c2h = n["task"].hash()
		with c3 :
			c3h = n["task"].hash()

		self.assertEqual( c1h, c2h )
		self.assertEqual( c1h, c3h )

		# Hashes that do use the context differ
		n2 = GafferDispatchTest.LoggingTaskNode()
		n2["frameSensitivePlug"] = Gaffer.StringPlug( defaultValue = "####" )
		with c1 :
			c1h = n2["task"].hash()
		with c2 :
			c2h = n2["task"].hash()
		with c3 :
			c3h = n2["task"].hash()

		self.assertNotEqual( c1h, c2h )
		self.assertNotEqual( c1h, c3h )

		# Hashes match across the same node type
		n3 = GafferDispatchTest.LoggingTaskNode()
		n3["frameSensitivePlug"] = Gaffer.StringPlug( defaultValue = "####" )
		with c1 :
			c1h2 = n3["task"].hash()
		with c2 :
			c2h2 = n3["task"].hash()
		with c3 :
			c3h2 = n3["task"].hash()

		self.assertEqual( c1h, c1h2 )
		self.assertEqual( c2h, c2h2 )
		self.assertEqual( c3h, c3h2 )

		# Hashes differ across different node types
		class MyNode( GafferDispatchTest.LoggingTaskNode ) :
			def __init__( self ) :
				GafferDispatchTest.LoggingTaskNode.__init__( self )

		IECore.registerRunTimeTyped( MyNode )

		n4 = MyNode()
		n4["frameSensitivePlug"] = Gaffer.StringPlug( defaultValue = "####" )
		with c1 :
			c1h3 = n4["task"].hash()
		with c2 :
			c2h3 = n4["task"].hash()
		with c3 :
			c3h3 = n4["task"].hash()

		self.assertNotEqual( c1h3, c1h2 )
		self.assertNotEqual( c2h3, c2h2 )
		self.assertNotEqual( c3h3, c3h2 )

	def testExecute( self ) :

		n = GafferDispatchTest.LoggingTaskNode()
		self.assertEqual( len( n.log ), 0 )

		n["task"].execute()
		self.assertEqual( len( n.log ), 1 )

		n["task"].execute()
		self.assertEqual( len( n.log ), 2 )

		c = Gaffer.Context()
		c.setFrame( Gaffer.Context.current().getFrame() + 1 )
		with c :
			n["task"].execute()
		self.assertEqual( len( n.log ), 3 )

	def testExecuteSequence( self ) :

		n = GafferDispatchTest.LoggingTaskNode()
		self.assertEqual( len( n.log ), 0 )

		n["task"].executeSequence( [ 1, 2, 3 ] )
		self.assertEqual( len( n.log ), 3 )

		n["task"].executeSequence( [ 1, 5, 10 ] )
		self.assertEqual( len( n.log ), 6 )

		n2 = GafferDispatchTest.LoggingTaskNode()
		n2["requiresSequenceExecution"].setValue( True )
		self.assertEqual( len( n2.log ), 0 )

		n2["task"].executeSequence( [ 1, 2, 3 ] )
		self.assertEqual( len( n2.log ), 1 )

		n2["task"].executeSequence( [ 1, 5, 10 ] )
		self.assertEqual( len( n2.log ), 2 )

	def testRequiresSequenceExecution( self ) :

		n = GafferDispatchTest.LoggingTaskNode()
		self.assertEqual( n.requiresSequenceExecution(), False )

	def testPreTasks( self ) :

		c1 = Gaffer.Context()
		c1.setFrame( 1 )
		c2 = Gaffer.Context()
		c2.setFrame( 2 )

		n = GafferDispatchTest.LoggingTaskNode()
		n2 = GafferDispatchTest.LoggingTaskNode()

		# make n2 require n
		n2["preTasks"][0].setInput( n["task"] )

		with c1 :
			self.assertEqual( n["task"].preTasks(), [] )
			self.assertEqual( n2["task"].preTasks(), [ GafferDispatch.TaskNode.Task( n, c1 ) ] )
		with c2 :
			self.assertEqual( n2["task"].preTasks(), [ GafferDispatch.TaskNode.Task( n, c2 ) ] )

	def testTaskConstructors( self ) :

		c = Gaffer.Context()

		n = GafferDispatchTest.LoggingTaskNode()
		t = GafferDispatch.TaskNode.Task( n, c )
		t2 = GafferDispatch.TaskNode.Task( n, c )
		t3 = GafferDispatch.TaskNode.Task( t2 )

		self.assertEqual( t.node(), n )
		self.assertEqual( t.context(), c )
		self.assertEqual( t2.node(), n )
		self.assertEqual( t2.context(), c )
		self.assertEqual( t3.node(), n )
		self.assertEqual( t3.context(), c )

	def testTaskComparison( self ) :

		c = Gaffer.Context()
		n = GafferDispatchTest.LoggingTaskNode()
		t1 = GafferDispatch.TaskNode.Task( n, c )
		t2 = GafferDispatch.TaskNode.Task( n, c )
		c2 = Gaffer.Context()
		c2["a"] = 2
		t3 = GafferDispatch.TaskNode.Task( n, c2 )
		n2 = GafferDispatchTest.LoggingTaskNode()
		t4 = GafferDispatch.TaskNode.Task( n2, c2 )

		self.assertEqual( t1, t1 )
		self.assertEqual( t1, t2 )
		self.assertEqual( t2, t1 )
		self.assertNotEqual( t1, t3 )
		self.assertNotEqual( t3, t1 )
		self.assertNotEqual( t3, t4 )
		self.assertNotEqual( t4, t3 )

	def testTaskSet( self ) :

		# A no-op TaskNode doesn't actually compute anything, so all tasks are the same
		c = Gaffer.Context()
		n = GafferDispatchTest.LoggingTaskNode()
		n["noOp"].setValue( True )
		t1 = GafferDispatch.TaskNode.Task( n, c )
		t2 = GafferDispatch.TaskNode.Task( n, c )
		self.assertEqual( t1, t2 )
		c2 = Gaffer.Context()
		c2["a"] = 2
		t3 = GafferDispatch.TaskNode.Task( n, c2 )
		self.assertEqual( t1, t3 )
		n2 = GafferDispatchTest.LoggingTaskNode()
		n2["noOp"].setValue( True )
		t4 = GafferDispatch.TaskNode.Task( n2, c2 )
		self.assertEqual( t1, t4 )
		t5 = GafferDispatch.TaskNode.Task( n2, c )
		self.assertEqual( t1, t5 )

		s = set( [ t1, t2, t3, t4, t4, t4, t1, t2, t4, t3, t2 ] )
		# there should only be 1 task because they all have identical results
		self.assertEqual( len(s), 1 )
		self.assertEqual( s, set( [ t1 ] ) )
		self.assertTrue( t1 in s )
		self.assertTrue( t2 in s )
		self.assertTrue( t3 in s )
		self.assertTrue( t4 in s )
		# even t5 is in there, because it's really the same task
		self.assertTrue( t5 in s )

		# MyNode.hash() depends on the context time, so tasks will vary
		my = GafferDispatchTest.LoggingTaskNode()
		my["frameSensitivePlug"] = Gaffer.StringPlug( defaultValue = "####" )
		c.setFrame( 1 )
		t1 = GafferDispatch.TaskNode.Task( my, c )
		t2 = GafferDispatch.TaskNode.Task( my, c )
		self.assertEqual( t1, t2 )
		c2 = Gaffer.Context()
		c2.setFrame( 2 )
		t3 = GafferDispatch.TaskNode.Task( my, c2 )
		self.assertNotEqual( t1, t3 )
		my2 = GafferDispatchTest.LoggingTaskNode()
		my2["frameSensitivePlug"] = Gaffer.StringPlug( defaultValue = "####" )
		t4 = GafferDispatch.TaskNode.Task( my2, c2 )
		self.assertNotEqual( t1, t4 )
		self.assertEqual( t3, t4 )
		t5 = GafferDispatch.TaskNode.Task( my2, c )
		self.assertEqual( t1, t5 )
		self.assertNotEqual( t3, t5 )

		s = set( [ t1, t2, t3, t4, t4, t4, t1, t2, t4, t3, t2 ] )
		# t1 and t3 are the only distinct tasks
		self.assertEqual( len(s), 2 )
		self.assertEqual( s, set( [ t1, t3 ] ) )
		# but they still all have equivalent tasks in the set
		self.assertTrue( t1 in s )
		self.assertTrue( t2 in s )
		self.assertTrue( t3 in s )
		self.assertTrue( t4 in s )
		self.assertTrue( t5 in s )

	def testInputAcceptanceInsideBoxes( self ) :

		s = Gaffer.ScriptNode()

		s["a"] = GafferDispatchTest.TextWriter()
		s["b"] = GafferDispatchTest.TextWriter()
		s["n"] = Gaffer.Node()
		s["n"]["task"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )

		# the TaskNode shouldn't accept inputs from any old node

		self.assertTrue( s["b"]["preTasks"][0].acceptsInput( s["a"]["task"] ) )
		self.assertFalse( s["b"]["preTasks"][0].acceptsInput( s["n"]["task"] ) )

		# and that shouldn't change just because we happen to be inside a box

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["a"], s["b"], s["n"] ] ) )

		self.assertTrue( b["b"]["preTasks"][0].acceptsInput( b["a"]["task"] ) )
		self.assertFalse( b["b"]["preTasks"][0].acceptsInput( b["n"]["task"] ) )

	def testInputAcceptanceFromBoxes( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["task"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )
		s["a"] = GafferDispatchTest.TextWriter()

		s["b"] = Gaffer.Box()
		s["b"]["a"] = GafferDispatchTest.TextWriter()
		s["b"]["b"] = GafferDispatchTest.TextWriter()
		s["b"]["n"] = Gaffer.Node()
		s["b"]["n"]["task"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )
		s["b"]["in"] = s["b"]["a"]["preTasks"][0].createCounterpart( "in", Gaffer.Plug.Direction.In )
		s["b"]["out"] = s["b"]["a"]["task"].createCounterpart( "out", Gaffer.Plug.Direction.Out )

		# TaskNodes should accept connections speculatively from unconnected box inputs and outputs

		self.assertTrue( s["b"]["a"]["preTasks"][0].acceptsInput( s["b"]["in"] ) )
		self.assertTrue( s["a"]["preTasks"][0].acceptsInput( s["b"]["out"] ) )

		# But the promoted plugs shouldn't accept any old inputs.

		self.assertFalse( s["b"]["in"].acceptsInput( s["n"]["task"] ) )
		self.assertFalse( s["b"]["out"].acceptsInput( s["b"]["n"]["task"] ) )

		# We should be able to connect them up only to other appropriate requirement plugs.

		self.assertTrue( s["a"]["preTasks"][0].acceptsInput( s["b"]["out"] ) )

		s["c"] = GafferDispatchTest.TextWriter()
		s["b"]["in"].setInput( s["c"]["task"] )
		self.assertTrue( s["b"]["a"]["preTasks"][0].acceptsInput( s["b"]["in"] ) )

		s["b"]["out"].setInput( s["b"]["b"]["task"] )
		self.assertTrue( s["a"]["preTasks"][0].acceptsInput( s["b"]["out"] ) )

	def testInputAcceptanceFromDots( self ) :

		e1 = GafferDispatchTest.TextWriter()
		e2 = GafferDispatchTest.TextWriter()

		d1 = Gaffer.Dot()
		d1.setup( e1["task"] )

		self.assertTrue( e2["preTasks"][0].acceptsInput( d1["out"] ) )

		d1["in"].setInput( e1["task"] )

		self.assertTrue( e2["preTasks"][0].acceptsInput( d1["out"] ) )

	def testReferencePromotedPreTasksPlug( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["e"] = GafferDispatchTest.TextWriter()
		p = s["b"].promotePlug( s["b"]["e"]["preTasks"][0] )
		p.setName( "p" )

		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		s["e"] = GafferDispatchTest.TextWriter()

		s["r"]["p"].setInput( s["e"]["task"] )

	def testReferencePromotedPreTasksArrayPlug( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["e"] = GafferDispatchTest.TextWriter()
		p = s["b"].promotePlug( s["b"]["e"]["preTasks"] )
		p.setName( "p" )

		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		s["e"] = GafferDispatchTest.TextWriter()

		s["r"]["p"][0].setInput( s["e"]["task"] )

		self.assertTrue( s["r"]["e"]["preTasks"][0].source().isSame( s["e"]["task"] ) )

	def testLoadPromotedRequirementsFromVersion0_15( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( os.path.dirname( __file__ ) + "/scripts/promotedRequirementsVersion-0.15.0.0.gfr" )
		s.load()

	def testLoadPromotedRequirementsNetworkFromVersion0_15( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( os.path.dirname( __file__ ) + "/scripts/promotedRequirementsNetworkVersion-0.15.0.0.gfr" )
		s.load()

	def testPostTasks( self ) :

		preWriter = GafferDispatchTest.TextWriter()
		postWriter = GafferDispatchTest.TextWriter()

		writer = GafferDispatchTest.TextWriter()
		writer["preTasks"][0].setInput( preWriter["task"] )
		writer["postTasks"][0].setInput( postWriter["task"] )

		c = Gaffer.Context()
		c["test"] = "test"
		with c :
			self.assertEqual( writer["task"].preTasks(), [ GafferDispatch.TaskNode.Task( preWriter, c ) ] )
			self.assertEqual( writer["task"].postTasks(), [ GafferDispatch.TaskNode.Task( postWriter, c ) ] )

	def testLoadNetworkFromVersion0_19( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( os.path.dirname( __file__ ) + "/scripts/version-0.19.0.0.gfr" )
		s.load()

		self.assertEqual( len( s["TaskList"]["preTasks"] ), 2 )
		self.assertEqual( s["TaskList"]["preTasks"][0].getName(), "preTask0" )
		self.assertEqual( s["TaskList"]["preTasks"][1].getName(), "preTask1" )

		self.assertTrue( s["TaskList"]["preTasks"][0].getInput().isSame( s["SystemCommand"]["task"] ) )
		self.assertTrue( s["TaskList"]["preTasks"][1].getInput() is None )

	def testExecuteSequenceWithIterable( self ) :

		n = GafferDispatchTest.LoggingTaskNode()

		n["task"].executeSequence( tuple( [ 1, 2, 3 ] ) )
		self.assertEqual( len( n.log ), 3 )

		n["task"].executeSequence( itertools.chain( [ 1, 2, 3 ], [ 4, 5, 6 ] ) )
		self.assertEqual( len( n.log ), 9 )

if __name__ == "__main__":
	unittest.main()
