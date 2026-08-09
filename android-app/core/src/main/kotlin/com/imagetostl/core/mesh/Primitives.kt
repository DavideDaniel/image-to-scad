package com.imagetostl.core.mesh

import com.imagetostl.core.csg.Polygon
import com.imagetostl.core.geom.Vec3
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.PI

object Primitives {

    /** Axis-aligned box, [size] = full extents (x, y, z), centered at [center]. */
    fun box(size: Vec3, center: Vec3): List<Polygon> {
        val hx = size.x / 2.0
        val hy = size.y / 2.0
        val hz = size.z / 2.0

        fun corner(sx: Int, sy: Int, sz: Int) =
            Vec3(center.x + sx * hx, center.y + sy * hy, center.z + sz * hz)

        // Corners indexed by sign combination.
        val c = mapOf(
            "---" to corner(-1, -1, -1), "+--" to corner(1, -1, -1),
            "++-" to corner(1, 1, -1), "-+-" to corner(-1, 1, -1),
            "--+" to corner(-1, -1, 1), "+-+" to corner(1, -1, 1),
            "+++" to corner(1, 1, 1), "-++" to corner(-1, 1, 1),
        )

        return listOf(
            // -X face (normal -x): CCW when viewed from -x looking toward +x
            Polygon(listOf(c["---"]!!, c["--+"]!!, c["-++"]!!, c["-+-"]!!)),
            // +X face
            Polygon(listOf(c["+-+"]!!, c["+--"]!!, c["++-"]!!, c["+++"]!!)),
            // -Y face
            Polygon(listOf(c["--+"]!!, c["---"]!!, c["+--"]!!, c["+-+"]!!)),
            // +Y face
            Polygon(listOf(c["-+-"]!!, c["-++"]!!, c["+++"]!!, c["++-"]!!)),
            // -Z face
            Polygon(listOf(c["---"]!!, c["-+-"]!!, c["++-"]!!, c["+--"]!!)),
            // +Z face
            Polygon(listOf(c["--+"]!!, c["+-+"]!!, c["+++"]!!, c["-++"]!!)),
        )
    }

    /**
     * Cylinder (or disc, if [depth] is small) of [radius] and [depth] extruded
     * along [axis] ("x" | "y" | "z"), centered at [center], tessellated with
     * [segments] sides.
     */
    fun cylinder(radius: Double, depth: Double, center: Vec3, axis: String, segments: Int): List<Polygon> {
        require(segments >= 3) { "cylinder needs >= 3 segments" }
        // Build in local space with the extrusion axis along local Z, then map into world axis.
        // Must be an orientation-preserving (det=+1) axis permutation, i.e. a cyclic
        // rotation, or the side-quad winding flips and normals point inward.
        val toWorld: (Double, Double, Double) -> Vec3 = when (axis.lowercase()) {
            "x" -> { lx, ly, lz -> Vec3(center.x + lz, center.y + lx, center.z + ly) }
            "y" -> { lx, ly, lz -> Vec3(center.x + ly, center.y + lz, center.z + lx) }
            else -> { lx, ly, lz -> Vec3(center.x + lx, center.y + ly, center.z + lz) }
        }

        val half = depth / 2.0
        val bottom = (0 until segments).map { i ->
            val a = 2.0 * PI * i / segments
            toWorld(radius * cos(a), radius * sin(a), -half)
        }
        val top = (0 until segments).map { i ->
            val a = 2.0 * PI * i / segments
            toWorld(radius * cos(a), radius * sin(a), half)
        }

        val polygons = mutableListOf<Polygon>()
        // Bottom cap: winding reversed so the face normal points toward -local Z.
        polygons.add(Polygon(bottom.reversed()))
        // Top cap.
        polygons.add(Polygon(top))
        // Side quads.
        for (i in 0 until segments) {
            val j = (i + 1) % segments
            polygons.add(Polygon(listOf(bottom[i], bottom[j], top[j], top[i])))
        }
        return polygons
    }
}
