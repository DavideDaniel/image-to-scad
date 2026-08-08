package com.imagetostl.core

import com.imagetostl.core.assembly.PlanBuilder
import com.imagetostl.core.plan.PlanParameter
import com.imagetostl.core.plan.editableParameters
import com.imagetostl.core.plan.parseComponentPlan
import com.imagetostl.core.plan.withParameterValue
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class PlanParametersTest {

    private fun loadPlan(name: String) =
        parseComponentPlan(javaClass.classLoader.getResourceAsStream(name)!!.readBytes().decodeToString())

    @Test
    fun `circular_shelf_poc exposes a slider per cylinder radius and depth`() {
        val plan = loadPlan("circular_shelf_plan.json")
        val params = plan.editableParameters()
        // 5 components (all cylinders) x 2 fields + 1 cut (cylinder) x 2 fields = 12
        assertEquals(12, params.size)
        assertTrue(params.all { it.field == PlanParameter.Field.RADIUS || it.field == PlanParameter.Field.DEPTH })
    }

    @Test
    fun `stand_plan exposes a slider per box dimension and per cylinder radius+depth, including cuts`() {
        val plan = loadPlan("stand_plan.json")
        val params = plan.editableParameters()
        val all = plan.model.components + plan.model.cuts
        val expected = all.fold(0) { acc, c -> acc + if (c.type == "box") 3 else 2 }
        assertEquals(expected, params.size)
    }

    @Test
    fun `withParameterValue only changes the targeted dimension and rebuilds correctly`() {
        val plan = loadPlan("circular_shelf_plan.json")
        val baseDiscRadiusParam = plan.editableParameters()
            .first { it.componentIndex == 0 && it.field == PlanParameter.Field.RADIUS }
        assertEquals(125.0, baseDiscRadiusParam.value)

        val edited = plan.withParameterValue(baseDiscRadiusParam, 200.0)
        assertEquals(200.0, edited.model.components[0].radius)
        // Every other field is untouched.
        assertEquals(plan.model.components[0].depth, edited.model.components[0].depth)
        assertEquals(plan.model.components.drop(1), edited.model.components.drop(1))

        val mesh = PlanBuilder.build(edited)
        val (min, max) = mesh.bounds()
        assertTrue(max.x - min.x > 300.0, "expected the enlarged base disc to widen the model")
    }
}
