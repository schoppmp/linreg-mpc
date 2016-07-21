function T = mytypes(dt,b,frac)
  switch dt
    case 'double'
      T = double([]);
    case 'single'
      T = single([]);
    case 'fixed'
      T = fi([],true,b,frac);
    case 'scaled'
      T = fi([],true,16,15,'DataType','ScaledDouble');
  end
end