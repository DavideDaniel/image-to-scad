package com.imagetostl.core.assembly

import com.imagetostl.core.csg.Csg
import com.imagetostl.core.geom.Vec3
import com.imagetostl.core.mesh.Mesh
import com.imagetostl.core.mesh.Primitives
import com.imagetostl.core.mesh.toMesh
import com.imagetostl.core.plan.Component
import com.imagetostl.core.plan.ComponentPlan

private const val DEFAULT_CYLINDER_SEGMENTS = 64

/** Builds a `component-plan/v0` into a triangle mesh: components unioned in order, then cuts subtracted. */
object PlanBuilder {

    fun build(plan: ComponentPlan): Mesh = buildCsg(plan).polygons.toMesh()

    fun buildCsg(plan: ComponentPlan): Csg {
        val model = plan.model
        require(model.components.isNotEmpty()) { "plan '${model.name}' has no components" }

        var solid = componentCsg(model.components[0])
        for (component in model.components.drop(1)) {
            solid = solid.union(componentCsg(component))
        }
        for (cut in model.cuts) {
            solid = solid.subtract(componentCsg(cut))
        }
        return solid
    }

    private fun componentCsg(c: Component): Csg {
        val center = Vec3(c.center[0], c.center[1], c.center[2])
        val polygons = when (c.type) {
            "box" -> {
                val s = requireNotNull(c.size) { "component '${c.name}' is type box but has no size" }
                Primitives.box(Vec3(s[0], s[1], s[2]), center)
            }
            "cylinder" -> {
                val radius = requireNotNull(c.radius) { "component '${c.name}' is type cylinder but has no radius" }
                val depth = requireNotNull(c.depth) { "component '${c.name}' is type cylinder but has no depth" }
                Primitives.cylinder(radius, depth, center, c.axis ?: "z", c.vertices ?: DEFAULT_CYLINDER_SEGMENTS)
            }
            else -> error("unknown component type '${c.type}' on '${c.name}'")
        }
        return Csg.fromPolygons(polygons)
    }
}
