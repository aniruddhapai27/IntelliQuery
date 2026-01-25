const Card = ({ children, className = "", hover = false, ...props }) => {
  const hoverClass = hover
    ? "hover:border-yellow-500/50 hover:shadow-2xl hover:shadow-yellow-600/20 hover:-translate-y-1"
    : "";

  const clickableClass = props.onClick ? "cursor-pointer" : "";

  return (
    <div
      className={`
      bg-gradient-to-br from-gray-900 to-black border border-yellow-600/30 rounded-xl p-6
      shadow-xl transition-all duration-300 ${hoverClass} ${clickableClass} ${className}
    `}
      {...props}
    >
      {children}
    </div>
  );
};

export default Card;
