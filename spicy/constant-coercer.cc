
#include "constant-coercer.h"
#include "constant.h"
#include "expression.h"
#include "type.h"

using namespace spicy;

void ConstantCoercer::visit(constant::Integer* i)
{
    setResult(nullptr);

    auto dst_i = ast::rtti::tryCast<type::Integer>(arg1());

    if ( dst_i ) {
        if ( dst_i->width() == 64 ||
             (i->value() <= 1l << dst_i->width() && i->value() >= -(1l << dst_i->width())) ) {
            auto c = new constant::Integer(i->value(), dst_i->width(), i->location());
            setResult(shared_ptr<Constant>(c));
        }

        return;
    }

    auto dst_b = ast::rtti::tryCast<type::Bool>(arg1());

    if ( dst_b ) {
        auto c = new constant::Bool(i->value() != 0, i->location());
        setResult(shared_ptr<Constant>(c));
    }

    auto dst_d = ast::rtti::tryCast<type::Double>(arg1());

    if ( dst_d ) {
        auto c = new constant::Double(i->value(), i->location());
        setResult(shared_ptr<Constant>(c));
    }
}

void ConstantCoercer::visit(constant::Tuple* t)
{
    setResult(nullptr);

    auto dst = ast::rtti::tryCast<type::Tuple>(arg1());

    if ( ! dst )
        return;

    if ( dst->wildcard() ) {
        setResult(t->sharedPtr<constant::Tuple>());
        return;
    }

    auto dst_types = dst->typeList();

    if ( dst_types.size() != t->value().size() )
        return;

    auto d = dst_types.begin();
    expression_list coerced_elems;

    for ( auto e : t->value() ) {
        auto coerced = e->coerceTo(*d++);
        if ( ! coerced )
            return;

        coerced_elems.push_back(coerced);
    }

    setResult(shared_ptr<Constant>(new constant::Tuple(coerced_elems, t->location())));
}

void ConstantCoercer::visit(constant::Optional* t)
{
    auto dst = ast::rtti::tryCast<type::Optional>(arg1());

    if ( dst ) {
        auto coerced = t->value()->coerceTo(dst->argType());
        setResult(std::make_shared<constant::Optional>(coerced));
        return;
    }
}
