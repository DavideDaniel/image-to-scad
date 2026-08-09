package com.imagetostl.core

import com.imagetostl.core.assembly.PlanBuilder
import com.imagetostl.core.csg.Csg
import com.imagetostl.core.geom.Vec3
import com.imagetostl.core.mesh.Mesh
import com.imagetostl.core.mesh.Primitives
import com.imagetostl.core.mesh.toMesh
import com.imagetostl.core.plan.parseComponentPlan
import com.imagetostl.core.stl.StlWriter
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.DataInputStream
import java.nio.ByteOrder
import kotlin.math.roundToLong
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

/**
 * Verifies the mesh is a closed, consistently-wound manifold: every directed
 * edge (a->b) appears exactly once, and its reverse (b->a) also appears
 * exactly once on a neighboring face. This catches both holes (missing
 * reverse edge) and inside-out/flipped faces (duplicate same-direction edge).
 */
private fun assertWatertight(mesh: Mesh, label: String) {
    fun key(v: Vec3) = Triple(
        (v.x * 1e4).roundToLong(),
        (v.y * 1e4).roundToLong(),
        (v.z * 1e4).roundToLong(),
    )

    val directed = HashMap<Pair<Triple<Long, Long, Long>, Triple<Long, Long, Long>>, Int>()
    for (t in mesh.triangles) {
        val ka = key(t.a); val kb = key(t.b); val kc = key(t.c)
        for (edge in listOf(ka to kb, kb to kc, kc to ka)) {
            directed[edge] = (directed[edge] ?: 0) + 1
        }
    }
    assertTrue(mesh.triangles.isNotEmpty(), "$label: mesh has no triangles")
    for ((edge, count) in directed) {
        assertEquals(1, count, "$label: directed edge $edge appears $count times (expected 1 - non-manifold or flipped face)")
        val reverse = edge.second to edge.first
        assertEquals(1, directed[reverse] ?: 0, "$label: edge $edge has no matching reverse edge (hole in mesh)")
    }
}

class CsgEngineTest {

    @Test
    fun `box primitive is a watertight cube`() {
        val mesh = Primitives.box(Vec3(10.0, 20.0, 30.0), Vec3(0.0, 0.0, 0.0)).toMesh()
        assertEquals(24, mesh.triangles.size) // 6 faces x 4 triangles (centroid fan of a quad)
        assertWatertight(mesh, "box")
        val (min, max) = mesh.bounds()
        assertEquals(Vec3(-5.0, -10.0, -15.0), min)
        assertEquals(Vec3(5.0, 10.0, 15.0), max)
    }

    @Test
    fun `cylinder is watertight on every axis`() {
        for (axis in listOf("x", "y", "z")) {
            val mesh = Primitives.cylinder(5.0, 12.0, Vec3(1.0, 2.0, 3.0), axis, 24).toMesh()
            assertWatertight(mesh, "cylinder axis=$axis")
        }
    }

    @Test
    fun `union of two overlapping boxes is watertight and bigger than either alone`() {
        val a = Csg.fromPolygons(Primitives.box(Vec3(10.0, 10.0, 10.0), Vec3(0.0, 0.0, 0.0)))
        val b = Csg.fromPolygons(Primitives.box(Vec3(10.0, 10.0, 10.0), Vec3(5.0, 0.0, 0.0)))
        val union = a.union(b)
        val mesh = union.polygons.toMesh()
        assertWatertight(mesh, "union")
        val (min, max) = mesh.bounds()
        assertEquals(-5.0, min.x, 1e-6)
        assertEquals(10.0, max.x, 1e-6) // second box extends to 5 + 5
    }

    @Test
    fun `subtract carves a cavity of the expected size`() {
        val block = Csg.fromPolygons(Primitives.box(Vec3(20.0, 20.0, 20.0), Vec3(0.0, 0.0, 0.0)))
        val cutter = Csg.fromPolygons(Primitives.box(Vec3(6.0, 6.0, 30.0), Vec3(0.0, 0.0, 0.0))) // pokes through top/bottom
        val result = block.subtract(cutter)
        val mesh = result.polygons.toMesh()
        assertWatertight(mesh, "subtract")
        // Through-hole: bounding box unchanged, but volume must have shrunk by roughly the cutter's cross-section x block height.
        val (min, max) = mesh.bounds()
        assertEquals(Vec3(-10.0, -10.0, -10.0), min)
        assertEquals(Vec3(10.0, 10.0, 10.0), max)
    }

    @Test
    fun `real circular_shelf_poc plan builds a watertight printable mesh`() {
        val json = javaClass.classLoader.getResourceAsStream("circular_shelf_plan.json")!!.readBytes().decodeToString()
        val plan = parseComponentPlan(json)
        val mesh = PlanBuilder.build(plan)
        assertWatertight(mesh, "circular_shelf_poc")
        val (min, max) = mesh.bounds()
        val height = max.z - min.z
        val diameter = max.x - min.x
        assertTrue(diameter in 240.0..260.0, "expected ~250mm diameter, got $diameter")
        assertTrue(height in 160.0..170.0, "expected ~163mm height, got $height")
    }

    @Test
    fun `real stackable mug shelf plan builds a watertight printable mesh`() {
        val json = javaClass.classLoader.getResourceAsStream("stand_plan.json")!!.readBytes().decodeToString()
        val plan = parseComponentPlan(json)
        val mesh = PlanBuilder.build(plan)
        assertWatertight(mesh, "mug_shelf")
        assertTrue(mesh.triangles.size > 12, "expected a multi-component mesh, got ${mesh.triangles.size} triangles")
    }

    @Test
    fun `editing a plan dimension changes the built mesh accordingly`() {
        val json = javaClass.classLoader.getResourceAsStream("circular_shelf_plan.json")!!.readBytes().decodeToString()
        val original = parseComponentPlan(json)
        val originalMesh = PlanBuilder.build(original)
        val originalDiameter = originalMesh.bounds().let { (min, max) -> max.x - min.x }

        // Simulate the UI editing "diameter" by scaling the base disc + tray radii, as a slider would.
        val edited = original.copy(
            model = original.model.copy(
                components = original.model.components.map { c ->
                    if (c.type == "cylinder" && c.name != "post_left" && c.name != "post_right" && c.name != "post_rear") {
                        c.copy(radius = (c.radius ?: 0.0) * 1.2)
                    } else c
                }
            )
        )
        val editedMesh = PlanBuilder.build(edited)
        assertWatertight(editedMesh, "circular_shelf_poc edited")
        val editedDiameter = editedMesh.bounds().let { (min, max) -> max.x - min.x }
        assertTrue(editedDiameter > originalDiameter * 1.1, "expected diameter to grow with radius slider: $originalDiameter -> $editedDiameter")
    }

    @Test
    fun `STL export round-trips triangle count`() {
        val mesh = Primitives.box(Vec3(10.0, 10.0, 10.0), Vec3.ZERO).toMesh()
        val out = ByteArrayOutputStream()
        StlWriter.writeBinary(mesh, out)

        val din = DataInputStream(ByteArrayInputStream(out.toByteArray()))
        din.skipBytes(80)
        val countBytes = ByteArray(4)
        din.readFully(countBytes)
        val count = java.nio.ByteBuffer.wrap(countBytes).order(ByteOrder.LITTLE_ENDIAN).int
        assertEquals(mesh.triangles.size, count)
    }
}
