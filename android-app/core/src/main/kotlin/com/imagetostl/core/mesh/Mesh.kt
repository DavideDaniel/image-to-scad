package com.imagetostl.core.mesh

import com.imagetostl.core.csg.Polygon
import com.imagetostl.core.geom.Vec3

private const val STITCH_EPSILON = 1e-6
private const val MIN_TRIANGLE_AREA = 1e-9

data class Triangle(val a: Vec3, val b: Vec3, val c: Vec3) {
    fun normal(): Vec3 = ((b - a) cross (c - a)).normalized()
    fun area(): Double = ((b - a) cross (c - a)).length() * 0.5
}

data class Mesh(val triangles: List<Triangle>) {
    fun bounds(): Pair<Vec3, Vec3> {
        var minX = Double.MAX_VALUE; var minY = Double.MAX_VALUE; var minZ = Double.MAX_VALUE
        var maxX = -Double.MAX_VALUE; var maxY = -Double.MAX_VALUE; var maxZ = -Double.MAX_VALUE
        for (t in triangles) for (v in listOf(t.a, t.b, t.c)) {
            minX = minOf(minX, v.x); minY = minOf(minY, v.y); minZ = minOf(minZ, v.z)
            maxX = maxOf(maxX, v.x); maxY = maxOf(maxY, v.y); maxZ = maxOf(maxZ, v.z)
        }
        return Vec3(minX, minY, minZ) to Vec3(maxX, maxY, maxZ)
    }
}

/**
 * BSP-CSG naturally produces T-junctions: a face that's untouched by the other
 * solid stays as one long edge, while its neighbor across that edge got cut
 * into several shorter collinear pieces (e.g. a through-hole splits one side
 * of a face but not the far side, which never crossed a cutter plane). The
 * surface is still geometrically closed, but naive per-polygon triangulation
 * leaves a crack there. This reinserts every other polygon's vertices that
 * land exactly on a polygon's edge, so both sides tessellate the same segment
 * identically.
 */
private fun stitchTJunctions(polygons: List<Polygon>): List<Polygon> {
    val allPoints = polygons.flatMap { it.vertices }.distinct()

    return polygons.map { poly ->
        val verts = poly.vertices
        val stitched = mutableListOf<Vec3>()
        for (i in verts.indices) {
            val a = verts[i]
            val b = verts[(i + 1) % verts.size]
            stitched.add(a)
            val ab = b - a
            val lenSq = ab.dot(ab)
            if (lenSq < STITCH_EPSILON * STITCH_EPSILON) continue
            val onEdge = allPoints
                .filter { p ->
                    val t = (p - a).dot(ab) / lenSq
                    if (t <= STITCH_EPSILON || t >= 1.0 - STITCH_EPSILON) return@filter false
                    val proj = a + ab * t
                    (p - proj).length() < STITCH_EPSILON
                }
                .sortedBy { (it - a).dot(ab) }
            stitched.addAll(onEdge)
        }
        Polygon(stitched)
    }
}

/**
 * Fan-triangulates each (near-planar) CSG output polygon, after stitching T-junctions
 * so adjacent faces share a matching edge tessellation. Fans from the centroid rather
 * than vertex 0: a T-junction point stitched into the edge right after vertex 0 is
 * collinear with vertex 0 by construction, so a corner-fan would triangulate it into a
 * zero-area sliver and silently drop the very edge the stitch was meant to add.
 */
fun List<Polygon>.toMesh(): Mesh {
    val triangles = mutableListOf<Triangle>()
    for (poly in stitchTJunctions(this)) {
        val v = poly.vertices
        var cx = 0.0; var cy = 0.0; var cz = 0.0
        for (p in v) { cx += p.x; cy += p.y; cz += p.z }
        val centroid = Vec3(cx / v.size, cy / v.size, cz / v.size)
        for (i in v.indices) {
            val t = Triangle(centroid, v[i], v[(i + 1) % v.size])
            if (t.area() > MIN_TRIANGLE_AREA) triangles.add(t)
        }
    }
    return Mesh(triangles)
}
