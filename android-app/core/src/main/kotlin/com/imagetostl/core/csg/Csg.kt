package com.imagetostl.core.csg

import com.imagetostl.core.geom.Vec3
import kotlin.math.abs

/**
 * Constructive solid geometry via BSP trees — a Kotlin port of the classic
 * csg.js algorithm (Evan Wallace, public domain), operating on arbitrary
 * (near-)planar polygons rather than triangles so box/cylinder faces stay
 * as single faces until the final triangulation step.
 */

private const val EPSILON = 1e-5

data class Plane(val normal: Vec3, val w: Double) {
    fun flip() = Plane(-normal, -w)

    /**
     * Splits [polygon] by this plane, distributing the pieces into the
     * four output lists. Coplanar polygons go to [coplanarFront] or
     * [coplanarBack] depending on whether they face the same way as this
     * plane; everything else goes to [front] and/or [back] (both, if the
     * polygon straddles the plane — new vertices are interpolated at the
     * crossing points).
     */
    fun splitPolygon(
        polygon: Polygon,
        coplanarFront: MutableList<Polygon>,
        coplanarBack: MutableList<Polygon>,
        front: MutableList<Polygon>,
        back: MutableList<Polygon>,
    ) {
        val COPLANAR = 0
        val FRONT = 1
        val BACK = 2
        val SPANNING = 3

        var polygonType = 0
        val types = IntArray(polygon.vertices.size)
        for (i in polygon.vertices.indices) {
            val t = normal.dot(polygon.vertices[i]) - w
            val type = if (t < -EPSILON) BACK else if (t > EPSILON) FRONT else COPLANAR
            polygonType = polygonType or type
            types[i] = type
        }

        when (polygonType) {
            COPLANAR -> {
                if (normal.dot(polygon.plane.normal) > 0) coplanarFront.add(polygon) else coplanarBack.add(polygon)
            }
            FRONT -> front.add(polygon)
            BACK -> back.add(polygon)
            else -> {
                val f = mutableListOf<Vec3>()
                val b = mutableListOf<Vec3>()
                val n = polygon.vertices.size
                for (i in 0 until n) {
                    val j = (i + 1) % n
                    val ti = types[i]
                    val tj = types[j]
                    val vi = polygon.vertices[i]
                    val vj = polygon.vertices[j]
                    if (ti != BACK) f.add(vi)
                    if (ti != FRONT) b.add(vi)
                    if ((ti or tj) == SPANNING) {
                        val t = (w - normal.dot(vi)) / normal.dot(vj - vi)
                        val v = vi.lerp(vj, t)
                        f.add(v)
                        b.add(v)
                    }
                }
                if (f.size >= 3) front.add(Polygon(f))
                if (b.size >= 3) back.add(Polygon(b))
            }
        }
    }

    companion object {
        fun fromPoints(a: Vec3, b: Vec3, c: Vec3): Plane {
            val n = ((b - a) cross (c - a)).normalized()
            return Plane(n, n.dot(a))
        }
    }
}

class Polygon(val vertices: List<Vec3>) {
    val plane: Plane = Plane.fromPoints(vertices[0], vertices[1], vertices[2])

    fun flip() = Polygon(vertices.reversed())
}

private class BspNode(polygons: List<Polygon> = emptyList()) {
    var plane: Plane? = null
    var front: BspNode? = null
    var back: BspNode? = null
    val polygons: MutableList<Polygon> = mutableListOf()

    init {
        if (polygons.isNotEmpty()) build(polygons)
    }

    fun clone(): BspNode {
        val n = BspNode()
        n.plane = plane
        n.front = front?.clone()
        n.back = back?.clone()
        n.polygons.addAll(polygons)
        return n
    }

    fun invert() {
        for (i in polygons.indices) polygons[i] = polygons[i].flip()
        plane = plane?.flip()
        front?.invert()
        back?.invert()
        val tmp = front
        front = back
        back = tmp
    }

    fun clipPolygons(input: List<Polygon>): List<Polygon> {
        val p = plane ?: return input.toList()
        val front = mutableListOf<Polygon>()
        val back = mutableListOf<Polygon>()
        for (poly in input) p.splitPolygon(poly, front, back, front, back)
        var frontOut: List<Polygon> = front
        var backOut: List<Polygon> = back
        this.front?.let { frontOut = it.clipPolygons(front) }
        backOut = this.back?.clipPolygons(back) ?: emptyList()
        return frontOut + backOut
    }

    fun clipTo(other: BspNode) {
        val clipped = other.clipPolygons(polygons)
        polygons.clear()
        polygons.addAll(clipped)
        front?.clipTo(other)
        back?.clipTo(other)
    }

    fun allPolygons(): List<Polygon> {
        val result = mutableListOf<Polygon>()
        result.addAll(polygons)
        front?.let { result.addAll(it.allPolygons()) }
        back?.let { result.addAll(it.allPolygons()) }
        return result
    }

    fun build(input: List<Polygon>) {
        if (input.isEmpty()) return
        if (plane == null) plane = input[0].plane
        val currentPlane = plane!!
        val f = mutableListOf<Polygon>()
        val b = mutableListOf<Polygon>()
        for (poly in input) currentPlane.splitPolygon(poly, polygons, polygons, f, b)
        if (f.isNotEmpty()) {
            if (front == null) front = BspNode()
            front!!.build(f)
        }
        if (b.isNotEmpty()) {
            if (back == null) back = BspNode()
            back!!.build(b)
        }
    }
}

/** Immutable solid represented as a soup of (near-)planar polygons. */
class Csg private constructor(val polygons: List<Polygon>) {

    fun union(other: Csg): Csg {
        val a = BspNode(polygons)
        val b = BspNode(other.polygons)
        a.clipTo(b)
        b.clipTo(a)
        b.invert()
        b.clipTo(a)
        b.invert()
        a.build(b.allPolygons())
        return Csg(a.allPolygons())
    }

    fun subtract(other: Csg): Csg {
        val a = BspNode(polygons)
        val b = BspNode(other.polygons)
        a.invert()
        a.clipTo(b)
        b.clipTo(a)
        b.invert()
        b.clipTo(a)
        b.invert()
        a.build(b.allPolygons())
        a.invert()
        return Csg(a.allPolygons())
    }

    fun intersect(other: Csg): Csg {
        val a = BspNode(polygons)
        val b = BspNode(other.polygons)
        a.invert()
        b.clipTo(a)
        b.invert()
        a.clipTo(b)
        b.clipTo(a)
        a.build(b.allPolygons())
        a.invert()
        return Csg(a.allPolygons())
    }

    companion object {
        fun fromPolygons(polygons: List<Polygon>) = Csg(polygons)
    }
}

/** Signed volume of a polygon soup via the divergence theorem (tetrahedra from the origin). Used only in tests. */
fun polygonVolume(polygons: List<Polygon>): Double {
    var vol = 0.0
    for (poly in polygons) {
        val v0 = poly.vertices[0]
        for (i in 1 until poly.vertices.size - 1) {
            val v1 = poly.vertices[i]
            val v2 = poly.vertices[i + 1]
            vol += (v0 cross v1).dot(v2) / 6.0
        }
    }
    return abs(vol)
}
